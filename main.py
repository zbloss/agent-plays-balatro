from game_state_agent import GameStateAgent

if __name__ == "__main__":
    master_agent = GameStateAgent()
    current_state = master_agent.extract_current_game_state()

    print("Current Game State:")
    print(f"  Player Hand: {current_state.player_hand}")
    print(f"  Active Jokers: {current_state.active_jokers}")
    print(f"  Deck Info: {current_state.deck_info}")
    print(f"  Score Info: {current_state.score_info}")
    print(f"  Hands Left: {current_state.hands_left}")
    print(f"  Discards Left: {current_state.discards_left}")
    print(f"  Raw Capture Data: {current_state.raw_capture_data}")
