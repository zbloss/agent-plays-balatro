from agent_plays_balatro.agents.game_state_agent import GameStateAgent
from agent_plays_balatro.models import (
    GameState,
)  # Optional: for type hinting if desired


def main():  # Wrapped in a main function
    master_agent = GameStateAgent()
    current_state: GameState = (
        master_agent.extract_current_game_state()
    )  # Added type hint

    print("Current Game State (Pydantic Model):")
    # Pydantic models have a good default __str__ and __repr__
    # For a more structured output, you can use .model_dump_json(indent=2) or .model_dump()
    print(current_state.model_dump_json(indent=2))

    # Alternatively, print fields individually if preferred:
    # print(f"  Player Hand: {current_state.player_hand}")
    # print(f"  Active Jokers: {current_state.active_jokers}")
    # print(f"  Deck Info: {current_state.deck_info}")
    # print(f"  Score Info: {current_state.score_info}")
    # print(f"  Hands Left: {current_state.hands_left}")
    # print(f"  Discards Left: {current_state.discards_left}")
    # print(f"  Raw Capture Data: {current_state.raw_capture_data}")


if __name__ == "__main__":
    main()
