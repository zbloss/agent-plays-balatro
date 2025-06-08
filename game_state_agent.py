from core_observer_agent import CoreObserverAgent
from image_processing_service import ImageProcessingService
from card_recognition_agent import CardRecognitionAgent
from joker_recognition_agent import JokerRecognitionAgent
from data_structures import Card, Joker, GameState

class GameStateAgent:
    def __init__(self):
        self.observer = CoreObserverAgent()
        self.image_processor = ImageProcessingService()
        self.card_recognizer = CardRecognitionAgent()
        self.joker_recognizer = JokerRecognitionAgent()

    def extract_current_game_state(self):
        capture_data = self.observer.capture_game_screen()
        regions = self.image_processor.identify_regions(capture_data)

        score_info = self.image_processor.extract_text_from_region(capture_data, "score_area")
        deck_info = self.image_processor.extract_text_from_region(capture_data, "deck_info_area")
        hands_left = self.image_processor.extract_text_from_region(capture_data, "hands_left_area")
        discards_left = self.image_processor.extract_text_from_region(capture_data, "discards_left_area")

        # In a real scenario, you'd pass a cropped image of the hand_area
        # For now, we pass the whole capture_data or region dictionary as a placeholder for the region data
        player_hand = self.card_recognizer.recognize_cards_in_region(regions.get("hand_area"))
        active_jokers = self.joker_recognizer.recognize_jokers_in_region(regions.get("joker_area"))

        return GameState(
            player_hand=player_hand,
            active_jokers=active_jokers,
            deck_info=deck_info,
            score_info=score_info,
            hands_left=hands_left,
            discards_left=discards_left,
            raw_capture_data=capture_data
        )
