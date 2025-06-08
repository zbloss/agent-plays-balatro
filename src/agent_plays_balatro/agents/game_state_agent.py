from agent_plays_balatro.agents.core_observer_agent import CoreObserverAgent
from agent_plays_balatro.tools.image_processing_service import ImageProcessingService
from agent_plays_balatro.agents.card_recognition_agent import CardRecognitionAgent
from agent_plays_balatro.agents.joker_recognition_agent import JokerRecognitionAgent
from agent_plays_balatro.models import GameState # Card, Joker no longer directly needed here for instantiation

class GameStateAgent:
    def __init__(self):
        self.observer = CoreObserverAgent()
        self.image_processor = ImageProcessingService()
        self.card_recognizer = CardRecognitionAgent()
        self.joker_recognizer = JokerRecognitionAgent()

    def extract_current_game_state(self) -> GameState: # Added return type hint
        capture_data = self.observer.capture_game_screen()
        regions = self.image_processor.identify_regions(capture_data)

        score_info = self.image_processor.extract_text_from_region(capture_data, "score_area")
        deck_info = self.image_processor.extract_text_from_region(capture_data, "deck_info_area")
        hands_left = self.image_processor.extract_text_from_region(capture_data, "hands_left_area")
        discards_left = self.image_processor.extract_text_from_region(capture_data, "discards_left_area")

        player_hand_data = self.card_recognizer.recognize_cards_in_region(regions.get("hand_area"))
        active_jokers_data = self.joker_recognizer.recognize_jokers_in_region(regions.get("joker_area"))

        # Pydantic models will perform validation on assignment
        # The actual Card and Joker objects are created in their respective recognizer agents
        return GameState(
            player_hand=player_hand_data,
            active_jokers=active_jokers_data,
            deck_info=deck_info,
            score_info=score_info,
            hands_left=hands_left,
            discards_left=discards_left,
            raw_capture_data=capture_data
        )
