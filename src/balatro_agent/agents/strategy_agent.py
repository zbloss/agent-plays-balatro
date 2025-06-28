import asyncio
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from collections import Counter
from itertools import combinations

from balatro_agent.models.game_models import (
    GameState, Card, Joker, Hand, PlayerStats, ShopState, BlindInfo,
    HandType, Suit, Rank
)


class HandEvaluator(BaseModel):
    """Evaluates poker hands and calculates scores with joker effects."""
    
    base_hand_scores: Dict[HandType, Tuple[int, int]] = Field(default_factory=lambda: {
        HandType.HIGH_CARD: (5, 1),
        HandType.PAIR: (10, 2),
        HandType.TWO_PAIR: (20, 2),
        HandType.THREE_OF_A_KIND: (30, 3),
        HandType.STRAIGHT: (30, 4),
        HandType.FLUSH: (35, 4),
        HandType.FULL_HOUSE: (40, 4),
        HandType.FOUR_OF_A_KIND: (60, 7),
        HandType.STRAIGHT_FLUSH: (100, 8),
        HandType.ROYAL_FLUSH: (100, 8),
        HandType.FIVE_OF_A_KIND: (120, 12),
        HandType.FLUSH_HOUSE: (140, 14),
        HandType.FLUSH_FIVE: (160, 16),
    })
    
    def identify_hand_type(self, cards: List[Card]) -> HandType:
        """Identify the type of poker hand."""
        if len(cards) < 1:
            return HandType.HIGH_CARD
        
        # Count ranks and suits
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        # Check for flushes
        is_flush = len(cards) >= 5 and max(suit_counts.values()) >= 5
        
        # Check for straights
        is_straight = self._is_straight(ranks)
        
        # Get rank count patterns
        count_values = sorted(rank_counts.values(), reverse=True)
        
        # Determine hand type
        if is_straight and is_flush:
            if self._is_royal(ranks):
                return HandType.ROYAL_FLUSH
            return HandType.STRAIGHT_FLUSH
        
        if count_values[0] == 5:
            if is_flush:
                return HandType.FLUSH_FIVE
            return HandType.FIVE_OF_A_KIND
        
        if count_values[0] == 4:
            return HandType.FOUR_OF_A_KIND
        
        if count_values[0] == 3:
            if is_flush and count_values[1] == 2:
                return HandType.FLUSH_HOUSE
            if count_values[1] == 2:
                return HandType.FULL_HOUSE
            return HandType.THREE_OF_A_KIND
        
        if is_flush:
            return HandType.FLUSH
        
        if is_straight:
            return HandType.STRAIGHT
        
        if count_values[0] == 2:
            if count_values[1] == 2:
                return HandType.TWO_PAIR
            return HandType.PAIR
        
        return HandType.HIGH_CARD
    
    def _is_straight(self, ranks: List[Rank]) -> bool:
        """Check if ranks form a straight."""
        if len(ranks) < 5:
            return False
        
        # Convert ranks to numerical values for easier straight detection
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13,
            Rank.ACE: 14
        }
        
        values = sorted(set(rank_values[rank] for rank in ranks))
        
        # Check for regular straight
        for i in range(len(values) - 4):
            if values[i+4] - values[i] == 4:
                return True
        
        # Check for Ace-low straight (A, 2, 3, 4, 5)
        if 14 in values and set([2, 3, 4, 5]).issubset(set(values)):
            return True
        
        return False
    
    def _is_royal(self, ranks: List[Rank]) -> bool:
        """Check if ranks form a royal flush (10, J, Q, K, A)."""
        royal_ranks = {Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}
        return royal_ranks.issubset(set(ranks))
    
    def calculate_hand_score(self, cards: List[Card], jokers: List[Joker]) -> Hand:
        """Calculate the complete score for a hand including joker effects."""
        hand_type = self.identify_hand_type(cards)
        base_chips, base_mult = self.base_hand_scores[hand_type]
        
        # Start with base values
        total_chips = base_chips
        total_mult = base_mult
        
        # Add card values
        for card in cards:
            total_chips += self._get_card_chip_value(card)
        
        # Apply joker effects
        total_chips, total_mult = self._apply_joker_effects(
            cards, jokers, total_chips, total_mult, hand_type
        )
        
        final_score = total_chips * total_mult
        
        return Hand(
            cards=cards,
            hand_type=hand_type,
            base_score=base_chips * base_mult,
            multiplier=total_mult,
            chips=total_chips,
            final_score=final_score
        )
    
    def _get_card_chip_value(self, card: Card) -> int:
        """Get the chip value of a card."""
        chip_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 10, Rank.QUEEN: 10, Rank.KING: 10,
            Rank.ACE: 11
        }
        return chip_values.get(card.rank, 0)
    
    def _apply_joker_effects(self, cards: List[Card], jokers: List[Joker], 
                           chips: int, mult: int, hand_type: HandType) -> Tuple[int, int]:
        """Apply joker effects to the hand score."""
        # This is a simplified implementation
        # In reality, each joker would have specific effects
        
        for joker in jokers:
            if not joker.active:
                continue
            
            # Example joker effects (would be much more complex in reality)
            if "chips" in joker.description.lower():
                chips += 30  # Example: +30 chips
            
            if "mult" in joker.description.lower():
                mult += 4  # Example: +4 mult
            
            if "pair" in joker.description.lower() and hand_type == HandType.PAIR:
                mult += 2  # Example: +2 mult for pairs
        
        return chips, mult


class StrategyAgent(BaseModel):
    """Agent responsible for making strategic decisions in Balatro."""
    
    hand_evaluator: HandEvaluator = Field(default_factory=HandEvaluator)
    risk_tolerance: float = Field(default=0.5, description="Risk tolerance from 0 (conservative) to 1 (aggressive)")
    
    def analyze_hand_potential(self, game_state: GameState) -> Dict[str, Any]:
        """Analyze the potential of the current hand."""
        hand = game_state.player_hand
        jokers = game_state.active_jokers
        
        if not hand:
            return {"best_hand": None, "score": 0, "recommendation": "wait"}
        
        # Find all possible hands (5 cards or less)
        possible_hands = []
        
        for size in range(1, min(6, len(hand) + 1)):
            for combo in combinations(hand, size):
                hand_result = self.hand_evaluator.calculate_hand_score(list(combo), jokers)
                possible_hands.append({
                    "cards": list(combo),
                    "hand_result": hand_result,
                    "score": hand_result.final_score
                })
        
        # Sort by score
        possible_hands.sort(key=lambda x: x["score"], reverse=True)
        
        best_hand = possible_hands[0] if possible_hands else None
        
        return {
            "best_hand": best_hand,
            "all_hands": possible_hands[:5],  # Top 5 hands
            "hand_count": len(possible_hands)
        }
    
    def should_play_hand(self, game_state: GameState) -> Dict[str, Any]:
        """Decide whether to play a hand or discard."""
        analysis = self.analyze_hand_potential(game_state)
        
        if not analysis["best_hand"]:
            return {"action": "discard", "reason": "No valid hands"}
        
        best_score = analysis["best_hand"]["score"]
        target_score = game_state.player_stats.target_score
        current_score = game_state.player_stats.current_score
        remaining_score = target_score - current_score
        hands_left = game_state.player_stats.hands_left
        
        # Calculate if this hand could win the round
        if best_score >= remaining_score:
            return {
                "action": "play",
                "cards": analysis["best_hand"]["cards"],
                "reason": f"Hand wins round with {best_score} points"
            }
        
        # Calculate expected value of playing vs discarding
        if hands_left <= 1:
            # Must play if it's the last hand
            return {
                "action": "play",
                "cards": analysis["best_hand"]["cards"],
                "reason": "Last hand - must play"
            }
        
        # Risk assessment
        score_efficiency = best_score / remaining_score
        
        if score_efficiency >= self.risk_tolerance:
            return {
                "action": "play",
                "cards": analysis["best_hand"]["cards"],
                "reason": f"Good score efficiency: {score_efficiency:.2f}"
            }
        
        # Consider discarding if we have discards left
        if game_state.can_discard():
            discard_cards = self._select_cards_to_discard(game_state)
            return {
                "action": "discard",
                "cards": discard_cards,
                "reason": "Hand not strong enough - discarding to improve"
            }
        
        # No discards left - play best available hand
        return {
            "action": "play",
            "cards": analysis["best_hand"]["cards"],
            "reason": "No discards left - playing best available"
        }
    
    def _select_cards_to_discard(self, game_state: GameState) -> List[Card]:
        """Select which cards to discard."""
        hand = game_state.player_hand
        
        # Simple strategy: discard cards that don't contribute to potential hands
        # In a more sophisticated version, this would analyze hand potential
        
        # Count ranks and suits
        ranks = [card.rank for card in hand]
        suits = [card.suit for card in hand]
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        discard_candidates = []
        
        for card in hand:
            # Keep cards that are part of pairs or potential flushes
            if rank_counts[card.rank] == 1 and suit_counts[card.suit] < 3:
                discard_candidates.append(card)
        
        # Discard up to 3 cards (or all candidates if fewer)
        return discard_candidates[:3]
    
    def evaluate_shop_purchases(self, game_state: GameState) -> List[Dict[str, Any]]:
        """Evaluate potential shop purchases."""
        recommendations = []
        shop = game_state.shop
        money = game_state.player_stats.money
        
        # Evaluate jokers
        for joker in shop.jokers:
            if joker.cost and joker.cost <= money:
                value = self._evaluate_joker_value(joker, game_state)
                recommendations.append({
                    "type": "joker",
                    "item": joker,
                    "value": value,
                    "cost": joker.cost,
                    "roi": value / joker.cost if joker.cost > 0 else 0
                })
        
        # Sort by ROI
        recommendations.sort(key=lambda x: x["roi"], reverse=True)
        
        return recommendations
    
    def _evaluate_joker_value(self, joker: Joker, game_state: GameState) -> float:
        """Evaluate the strategic value of a joker."""
        # Simplified joker evaluation
        # In reality, this would be much more sophisticated
        
        base_value = 50  # Base value for any joker
        
        # Bonus for rarity
        rarity_bonus = {
            "Common": 0,
            "Uncommon": 20,
            "Rare": 50,
            "Legendary": 100
        }
        base_value += rarity_bonus.get(joker.rarity, 0)
        
        # Bonus based on description keywords
        description_lower = joker.description.lower()
        
        if "mult" in description_lower:
            base_value += 30
        if "chips" in description_lower:
            base_value += 25
        if "money" in description_lower:
            base_value += 15
        
        return base_value
    
    def plan_ante_strategy(self, game_state: GameState) -> Dict[str, Any]:
        """Plan strategy for the current ante."""
        ante = game_state.player_stats.ante
        money = game_state.player_stats.money
        
        strategy = {
            "focus": "survival",
            "shop_budget": money * 0.7,  # Reserve some money
            "joker_priority": "score_boost",
            "risk_level": self.risk_tolerance
        }
        
        if ante <= 3:
            strategy["focus"] = "economy"
            strategy["shop_budget"] = money * 0.5
            strategy["joker_priority"] = "money_generation"
        elif ante <= 6:
            strategy["focus"] = "scaling"
            strategy["joker_priority"] = "score_multiplier"
        else:
            strategy["focus"] = "survival"
            strategy["shop_budget"] = money * 0.9
            strategy["joker_priority"] = "any_advantage"
        
        return strategy
