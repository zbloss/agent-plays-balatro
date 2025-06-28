import cv2
import numpy as np
from PIL import Image
import base64
import io
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field
import json
import asyncio
from pathlib import Path
import pyautogui

from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import ModelFamily, UserMessage
from balatro_agent.models.game_models import Card, Joker, Suit, Rank, PlayerStats, ShopState
from balatro_agent.config import Config


class VLMVisionProcessor(BaseModel):
    """Vision Language Model processor for Balatro game state analysis."""
    
    config: Config = Field(default_factory=Config)
    vlm_model: Optional[Any] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_vlm()
    
    def _initialize_vlm(self):
        """Initialize the Vision Language Model."""

        if not self.vlm_model:
            # Use a vision-capable model like minicpm-v
            self.vlm_model = OllamaChatCompletionClient(
                model="minicpm-v:8b",
                model_info={
                    "json_output": True,
                    "function_calling": False,
                    "vision": True,
                    "family": ModelFamily.UNKNOWN,
                    "structured_output": True,
                },
            )
    
    def _encode_image_to_base64(self, image: np.ndarray) -> str:
        """Convert numpy image to base64 string."""
        # Convert BGR to RGB if needed
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        return base64.b64encode(image_data).decode('utf-8')
    
    async def _query_vlm(self, image: np.ndarray, prompt: str) -> Optional[Dict[str, Any]]:
        """Query the Vision Language Model with an image and prompt."""
        if not self.vlm_model:
            print("❌ VLM not available")
            return None
        
        try:
            # Encode image
            image_base64 = self._encode_image_to_base64(image)
            
            # Create message with image
            message = UserMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                    }
                ],
                source="user"
            )
            
            # Query the model
            response = await self.vlm_model.create([message])
            
            # Parse JSON response
            if response.content:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    return {"text": response.content}
            
        except Exception as e:
            print(f"❌ VLM query failed: {e}")
        
        return None
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Take a screenshot of the game window."""
        screenshot = pyautogui.screenshot(region=region)
        return np.array(screenshot)
    
    async def analyze_full_game_state(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze the complete game state using VLM."""
        prompt = """
        Analyze this Balatro game screenshot and extract all game state information in JSON format.
        
        Please identify and return:
        {
          "player_stats": {
            "money": int,
            "ante": int,
            "hands_left": int,
            "discards_left": int,
            "current_score": int,
            "target_score": int
          },
          "cards_in_hand": [
            {
              "rank": "2-10, J, Q, K, A",
              "suit": "Hearts, Diamonds, Clubs, Spades",
              "position": [x, y]
            }
          ],
          "active_jokers": [
            {
              "name": "joker name",
              "description": "joker description",
              "position": [x, y]
            }
          ],
          "game_phase": "select, shop, boss, or other",
          "shop_items": {
            "jokers": [...],
            "cards": [...],
            "booster_packs": [...],
            "vouchers": [...]
          },
          "current_blind": {
            "name": "blind name",
            "type": "Small, Big, or Boss",
            "score_requirement": int,
            "reward": int
          }
        }
        
        Focus on accuracy. If you can't clearly see something, mark it as null or omit it.
        Pay special attention to card ranks and suits, joker names and effects.
        """
        
        return await self._query_vlm(image, prompt)
    
    async def detect_cards_in_hand(self, image: np.ndarray) -> List[Card]:
        """Detect cards in the player's hand using VLM."""
        prompt = """
        Analyze this Balatro game screenshot and identify all playing cards in the player's hand.
        
        Return a JSON array of cards:
        [
          {
            "rank": "2-10, J, Q, K, A",
            "suit": "Hearts, Diamonds, Clubs, Spades",
            "enhanced": false,
            "edition": null,
            "seal": null,
            "position": [x, y]
          }
        ]
        
        Be very careful about card identification. Look for:
        - Card rank (number or face card letter)
        - Card suit (red hearts/diamonds, black clubs/spades)
        - Any special effects (foil, holographic, etc.)
        - Exact position in the image
        
        Only include cards you can clearly identify.
        """
        
        result = await self._query_vlm(image, prompt)
        
        if not result:
            return []
        
        cards = []
        card_data = result.get('cards', result) if isinstance(result, dict) else result
        
        if isinstance(card_data, list):
            for card_info in card_data:
                try:
                    # Map string values to enums
                    rank_str = card_info.get('rank', '').upper()
                    suit_str = card_info.get('suit', '').title()
                    
                    # Convert rank
                    rank = None
                    if rank_str in ['A', 'ACE']:
                        rank = Rank.ACE
                    elif rank_str in ['K', 'KING']:
                        rank = Rank.KING
                    elif rank_str in ['Q', 'QUEEN']:
                        rank = Rank.QUEEN
                    elif rank_str in ['J', 'JACK']:
                        rank = Rank.JACK
                    elif rank_str.isdigit():
                        num = int(rank_str)
                        rank_map = {
                            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
                            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE, 10: Rank.TEN
                        }
                        rank = rank_map.get(num)
                    
                    # Convert suit
                    suit = None
                    if suit_str == 'Hearts':
                        suit = Suit.HEARTS
                    elif suit_str == 'Diamonds':
                        suit = Suit.DIAMONDS
                    elif suit_str == 'Clubs':
                        suit = Suit.CLUBS
                    elif suit_str == 'Spades':
                        suit = Suit.SPADES
                    
                    if rank and suit:
                        position = card_info.get('position')
                        card = Card(
                            rank=rank,
                            suit=suit,
                            enhanced=card_info.get('enhanced', False),
                            edition=card_info.get('edition'),
                            seal=card_info.get('seal'),
                            position=tuple(position) if position else None
                        )
                        cards.append(card)
                        
                except Exception as e:
                    print(f"⚠️ Error parsing card: {e}")
                    continue
        
        return cards
    
    async def detect_jokers(self, image: np.ndarray) -> List[Joker]:
        """Detect jokers in the current view using VLM."""
        prompt = """
        Analyze this Balatro game screenshot and identify all jokers visible on screen.
        
        Return a JSON array of jokers:
        [
          {
            "name": "exact joker name",
            "description": "joker effect description",
            "rarity": "Common, Uncommon, Rare, Legendary",
            "cost": price_if_in_shop,
            "position": [x, y]
          }
        ]
        
        Look for joker cards which typically have:
        - Distinctive artwork
        - Name at the top
        - Effect description below
        - Rarity indicated by border color
        - Price if in shop
        
        Be precise with joker names and descriptions as they affect game strategy.
        """
        
        result = await self._query_vlm(image, prompt)
        
        if not result:
            return []
        
        jokers = []
        joker_data = result.get('jokers', result) if isinstance(result, dict) else result
        
        if isinstance(joker_data, list):
            for joker_info in joker_data:
                try:
                    joker = Joker(
                        name=joker_info.get('name', 'Unknown'),
                        description=joker_info.get('description', ''),
                        rarity=joker_info.get('rarity', 'Common'),
                        cost=joker_info.get('cost'),
                        position=tuple(joker_info['position']) if joker_info.get('position') else None
                    )
                    jokers.append(joker)
                except Exception as e:
                    print(f"⚠️ Error parsing joker: {e}")
                    continue
        
        return jokers
    
    async def extract_game_stats(self, image: np.ndarray) -> Dict[str, int]:
        """Extract game statistics from the UI using VLM."""
        prompt = """
        Look at this Balatro game screenshot and extract the player statistics.
        
        Return JSON with these exact fields:
        {
          "money": dollars_amount,
          "ante": current_ante_number,
          "hands_left": remaining_hands,
          "discards_left": remaining_discards,
          "current_score": current_round_score,
          "target_score": target_score_for_blind
        }
        
        Look for these UI elements:
        - Money: Usually shows as $X in top area
        - Ante: Current ante level (1, 2, 3, etc.)
        - Hands: Remaining hands to play this round
        - Discards: Remaining discards this round
        - Score: Current score vs target score for the blind
        
        Return 0 for any values you cannot clearly see.
        """
        
        result = await self._query_vlm(image, prompt)
        
        if not result:
            return {}
        
        # Extract stats with defaults
        stats = {}
        if isinstance(result, dict):
            stats['money'] = result.get('money', 0)
            stats['ante'] = result.get('ante', 1)
            stats['hands_left'] = result.get('hands_left', 4)
            stats['discards_left'] = result.get('discards_left', 3)
            stats['current_score'] = result.get('current_score', 0)
            stats['target_score'] = result.get('target_score', 300)
        
        return stats
    
    async def detect_shop_items(self, image: np.ndarray) -> Dict[str, List]:
        """Detect items available in the shop using VLM."""
        prompt = """
        Analyze this Balatro shop screenshot and identify all purchasable items.
        
        Return JSON:
        {
          "jokers": [
            {"name": "joker_name", "description": "effect", "cost": price, "position": [x, y]}
          ],
          "cards": [
            {"rank": "card_rank", "suit": "card_suit", "cost": price, "position": [x, y]}
          ],
          "booster_packs": [
            {"name": "pack_name", "description": "pack_type", "cost": price, "position": [x, y]}
          ],
          "vouchers": [
            {"name": "voucher_name", "description": "effect", "cost": price, "position": [x, y]}
          ]
        }
        
        Look for:
        - Jokers with their names and effects
        - Playing cards with rank/suit
        - Booster packs (Arcana, Celestial, etc.)
        - Vouchers with permanent effects
        - Prices for each item
        - Reroll cost if visible
        """
        
        result = await self._query_vlm(image, prompt)
        
        if not result:
            return {
                'jokers': [],
                'cards': [],
                'booster_packs': [],
                'vouchers': []
            }
        
        return result if isinstance(result, dict) else {
            'jokers': [],
            'cards': [],
            'booster_packs': [],
            'vouchers': []
        }
    
    async def identify_game_phase(self, image: np.ndarray) -> str:
        """Determine the current game phase using VLM."""
        prompt = """
        Look at this Balatro game screenshot and determine the current game phase.
        
        Return one of these exact values:
        - "select": Player is selecting cards to play/discard
        - "shop": Player is in the shop between rounds
        - "boss": Boss blind is active
        - "pack": Opening a booster pack
        - "voucher": Voucher selection screen
        - "ante": Between ante progression
        - "game_over": Game has ended
        - "menu": In menus or settings
        
        Base your decision on visible UI elements:
        - Play/Discard buttons = "select"
        - Shop with items and reroll = "shop"
        - Boss blind description = "boss"
        - Pack opening interface = "pack"
        - Voucher selection = "voucher"
        """
        
        result = await self._query_vlm(image, prompt)
        
        if isinstance(result, dict):
            return result.get('phase', 'select')
        elif isinstance(result, str):
            return result.strip().lower()
        
        return 'select'  # Default fallback
    
    async def get_blind_info(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Extract information about the current blind using VLM."""
        prompt = """
        Analyze this Balatro screenshot for blind information.
        
        Return JSON:
        {
          "name": "blind_name",
          "type": "Small, Big, or Boss",
          "score_requirement": target_score,
          "reward": money_reward,
          "effect": "blind_special_effect_if_any"
        }
        
        Look for:
        - Blind name (Small Blind, Big Blind, or specific Boss name)
        - Score requirement to beat the blind
        - Money reward for winning
        - Any special effects (boss blinds have unique mechanics)
        """
        
        result = await self._query_vlm(image, prompt)
        
        if isinstance(result, dict):
            return {
                'name': result.get('name', 'Unknown'),
                'type': result.get('type', 'Small'),
                'score_requirement': result.get('score_requirement', 300),
                'reward': result.get('reward', 3),
                'effect': result.get('effect')
            }
        
        return None
