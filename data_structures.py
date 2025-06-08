from collections import namedtuple

Card = namedtuple('Card', ['rank', 'suit'])
Joker = namedtuple('Joker', ['name', 'description'])
GameState = namedtuple('GameState', [
    'player_hand',
    'active_jokers',
    'deck_info',
    'score_info',
    'hands_left',
    'discards_left',
    'raw_capture_data'
])
