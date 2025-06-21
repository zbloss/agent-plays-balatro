from typing import List
from pydantic import BaseModel


class Card(BaseModel):
    rank: str
    suit: str


class Joker(BaseModel):
    name: str
    description: str


class GameState(BaseModel):
    player_hand: List[Card]
    active_jokers: List[Joker]
    deck_info: str
    score_info: str
    hands_left: str
    discards_left: str
    raw_capture_data: str  # Placeholder for actual capture data type
