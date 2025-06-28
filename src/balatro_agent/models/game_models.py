from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class Suit(Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"


class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "Jack"
    QUEEN = "Queen"
    KING = "King"
    ACE = "Ace"


class HandType(Enum):
    HIGH_CARD = "High Card"
    PAIR = "Pair"
    TWO_PAIR = "Two Pair"
    THREE_OF_A_KIND = "Three of a Kind"
    STRAIGHT = "Straight"
    FLUSH = "Flush"
    FULL_HOUSE = "Full House"
    FOUR_OF_A_KIND = "Four of a Kind"
    STRAIGHT_FLUSH = "Straight Flush"
    ROYAL_FLUSH = "Royal Flush"
    FIVE_OF_A_KIND = "Five of a Kind"
    FLUSH_HOUSE = "Flush House"
    FLUSH_FIVE = "Flush Five"


class Card(BaseModel):
    rank: Rank
    suit: Suit
    enhanced: bool = False
    edition: Optional[str] = None  # e.g., "Foil", "Holographic", "Polychrome"
    seal: Optional[str] = None  # e.g., "Red", "Blue", "Gold", "Purple"
    position: Optional[tuple[int, int]] = None  # Screen coordinates if detected


class Joker(BaseModel):
    name: str
    description: str
    rarity: str = "Common"  # Common, Uncommon, Rare, Legendary
    cost: Optional[int] = None
    effect: Optional[str] = None
    position: Optional[tuple[int, int]] = None
    active: bool = True


class Hand(BaseModel):
    cards: List[Card]
    hand_type: HandType
    base_score: int
    multiplier: int
    chips: int
    final_score: int


class BlindInfo(BaseModel):
    name: str
    type: str  # Small, Big, Boss
    score_requirement: int
    reward: int
    effect: Optional[str] = None


class ShopState(BaseModel):
    jokers: List[Joker] = Field(default_factory=list)
    cards: List[Card] = Field(default_factory=list)
    booster_packs: List[str] = Field(default_factory=list)
    vouchers: List[str] = Field(default_factory=list)
    tarot_cards: List[str] = Field(default_factory=list)
    spectral_cards: List[str] = Field(default_factory=list)
    reroll_cost: int = 5


class PlayerStats(BaseModel):
    money: int = 0
    ante: int = 1
    hands_left: int = 4
    discards_left: int = 3
    current_score: int = 0
    target_score: int = 300
    round_number: int = 1


class GameState(BaseModel):
    player_hand: List[Card] = Field(default_factory=list)
    played_cards: List[Card] = Field(default_factory=list)
    active_jokers: List[Joker] = Field(default_factory=list)
    shop: ShopState = Field(default_factory=ShopState)
    current_blind: Optional[BlindInfo] = None
    player_stats: PlayerStats = Field(default_factory=PlayerStats)
    deck_size: int = 52
    game_phase: str = "select"  # select, play, shop, boss
    last_hand_played: Optional[Hand] = None
    screenshot_path: Optional[str] = None
    raw_capture_data: Optional[Dict[str, Any]] = None
    
    def can_play_hand(self) -> bool:
        """Check if player can play a hand."""
        return self.player_stats.hands_left > 0 and len(self.player_hand) > 0
    
    def can_discard(self) -> bool:
        """Check if player can discard cards."""
        return self.player_stats.discards_left > 0 and len(self.player_hand) > 0
    
    def has_winning_score(self) -> bool:
        """Check if current score meets the target."""
        return self.player_stats.current_score >= self.player_stats.target_score
