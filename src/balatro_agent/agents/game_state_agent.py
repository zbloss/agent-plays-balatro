import asyncio
import numpy as np
import cv2
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import UserMessage, SystemMessage

from balatro_agent.models.game_models import (
    GameState, Card, Joker, Hand, PlayerStats, ShopState, BlindInfo,
    HandType, Suit, Rank
)
from balatro_agent.tools.vlm_vision_processor import VLMVisionProcessor
from balatro_agent.config import Config


class GameStateAgent(BaseModel):
    """Agent responsible for maintaining and updating the game state."""
    
    game_state: GameState = Field(default_factory=GameState)
    vision_processor: VLMVisionProcessor = Field(default_factory=VLMVisionProcessor)
    config: Config = Field(default_factory=Config)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self.vision_processor = VLMVisionProcessor()
    
    async def update_game_state_from_screenshot(self, screenshot_path: Optional[str] = None) -> GameState:
        """Update the game state by analyzing a screenshot."""
        # Take screenshot if not provided
        if screenshot_path is None:
            screenshot = self.vision_processor.take_screenshot()
        else:
            screenshot = cv2.imread(screenshot_path)
        
        # Store screenshot info
        self.game_state.screenshot_path = screenshot_path
        
        # Extract game statistics
        stats = await self.vision_processor.extract_game_stats(screenshot)
        self._update_player_stats(stats)
        
        # Detect cards in hand
        cards_in_hand = await self.vision_processor.detect_cards_in_hand(screenshot)
        self.game_state.player_hand = cards_in_hand
        
        # Detect active jokers
        active_jokers = await self.vision_processor.detect_jokers(screenshot)
        self.game_state.active_jokers = active_jokers
        
        # Determine current game phase first
        await self._determine_game_phase(screenshot)
        
        # Detect shop items if in shop phase
        if self.game_state.game_phase == "shop":
            shop_items = await self.vision_processor.detect_shop_items(screenshot)
            self._update_shop_state(shop_items)
        
        # Get blind information
        blind_info = await self.vision_processor.get_blind_info(screenshot)
        if blind_info:
            blind = BlindInfo(
                name=blind_info['name'],
                type=blind_info['type'],
                score_requirement=blind_info['score_requirement'],
                reward=blind_info['reward'],
                effect=blind_info.get('effect')
            )
            self.set_current_blind(blind)
        
        return self.game_state
    
    def _update_player_stats(self, stats: Dict[str, int]) -> None:
        """Update player statistics from extracted data."""
        if 'money' in stats:
            self.game_state.player_stats.money = stats['money']
        if 'ante' in stats:
            self.game_state.player_stats.ante = stats['ante']
        if 'hands_left' in stats:
            self.game_state.player_stats.hands_left = stats['hands_left']
        if 'discards_left' in stats:
            self.game_state.player_stats.discards_left = stats['discards_left']
        if 'score' in stats:
            self.game_state.player_stats.current_score = stats['score']
    
    def _update_shop_state(self, shop_items: Dict[str, List]) -> None:
        """Update shop state from detected items."""
        self.game_state.shop.jokers = shop_items.get('jokers', [])
        self.game_state.shop.cards = shop_items.get('cards', [])
        self.game_state.shop.booster_packs = shop_items.get('booster_packs', [])
        self.game_state.shop.vouchers = shop_items.get('vouchers', [])
    
    async def _determine_game_phase(self, screenshot) -> None:
        """Determine the current game phase."""
        # Use VLM to identify the current game phase
        game_phase = await self.vision_processor.identify_game_phase(screenshot)
        self.game_state.game_phase = game_phase
    
    def update_hand_played(self, selected_cards: List[Card], hand_result: Hand) -> None:
        """Update state after a hand is played."""
        self.game_state.last_hand_played = hand_result
        self.game_state.played_cards.extend(selected_cards)
        
        # Remove played cards from hand
        for card in selected_cards:
            if card in self.game_state.player_hand:
                self.game_state.player_hand.remove(card)
        
        # Update hands left
        self.game_state.player_stats.hands_left -= 1
        
        # Update score
        self.game_state.player_stats.current_score += hand_result.final_score
    
    def update_cards_discarded(self, discarded_cards: List[Card]) -> None:
        """Update state after cards are discarded."""
        # Remove discarded cards from hand
        for card in discarded_cards:
            if card in self.game_state.player_hand:
                self.game_state.player_hand.remove(card)
        
        # Update discards left
        self.game_state.player_stats.discards_left -= 1
    
    def add_joker(self, joker: Joker) -> None:
        """Add a joker to active jokers."""
        self.game_state.active_jokers.append(joker)
    
    def remove_joker(self, joker_name: str) -> None:
        """Remove a joker by name."""
        self.game_state.active_jokers = [
            j for j in self.game_state.active_jokers 
            if j.name != joker_name
        ]
    
    def set_current_blind(self, blind: BlindInfo) -> None:
        """Set the current blind information."""
        self.game_state.current_blind = blind
        self.game_state.player_stats.target_score = blind.score_requirement
    
    def reset_for_new_round(self) -> None:
        """Reset state for a new round."""
        self.game_state.player_stats.hands_left = 4
        self.game_state.player_stats.discards_left = 3
        self.game_state.played_cards.clear()
        self.game_state.last_hand_played = None
        self.game_state.player_stats.current_score = 0
    
    def get_available_actions(self) -> List[str]:
        """Get list of currently available actions."""
        actions = []
        
        if self.game_state.game_phase == "select":
            if self.game_state.can_play_hand():
                actions.append("play_hand")
            if self.game_state.can_discard():
                actions.append("discard_cards")
        
        elif self.game_state.game_phase == "shop":
            actions.extend(["buy_joker", "buy_card", "buy_pack", "reroll", "skip_shop"])
        
        return actions
    
    def get_state_summary(self) -> str:
        """Get a human-readable summary of the current game state."""
        summary = f"""
Game State Summary:
- Phase: {self.game_state.game_phase}
- Money: ${self.game_state.player_stats.money}
- Ante: {self.game_state.player_stats.ante}
- Hands Left: {self.game_state.player_stats.hands_left}
- Discards Left: {self.game_state.player_stats.discards_left}
- Current Score: {self.game_state.player_stats.current_score}
- Target Score: {self.game_state.player_stats.target_score}
- Cards in Hand: {len(self.game_state.player_hand)}
- Active Jokers: {len(self.game_state.active_jokers)}
"""
        
        if self.game_state.current_blind:
            summary += f"- Current Blind: {self.game_state.current_blind.name} ({self.game_state.current_blind.type})\n"
        
        if self.game_state.last_hand_played:
            summary += f"- Last Hand: {self.game_state.last_hand_played.hand_type.value} for {self.game_state.last_hand_played.final_score} points\n"
        
        return summary.strip()
    
    def export_state(self) -> Dict[str, Any]:
        """Export the current game state as a dictionary."""
        return self.game_state.model_dump()
    
    def import_state(self, state_dict: Dict[str, Any]) -> None:
        """Import game state from a dictionary."""
        self.game_state = GameState.model_validate(state_dict)
