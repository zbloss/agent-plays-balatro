class ImageProcessingService:
    def __init__(self):
        pass

    def identify_regions(self, image_data):
        print(f"Identifying regions in {image_data}...")
        return {
            "hand_area": {"x": 100, "y": 500, "width": 600, "height": 150},
            "joker_area": {"x": 100, "y": 300, "width": 600, "height": 100},
            "score_area": {"x": 700, "y": 50, "width": 100, "height": 50},
            "deck_info_area": {"x": 50, "y": 50, "width": 150, "height": 50},
            "hands_left_area": {"x": 700, "y": 100, "width": 100, "height": 30},
            "discards_left_area": {"x": 700, "y": 130, "width": 100, "height": 30},
        }

    def extract_text_from_region(self, image_data, region_name):
        print(f"Extracting text from {region_name} in {image_data}...")
        if region_name == "score_area":
            return "300 / 12000"
        elif region_name == "deck_info_area":
            return "Deck: 25/52"
        elif region_name == "hands_left_area":
            return "Hands: 8"
        elif region_name == "discards_left_area":
            return "Discards: 3"
        else:
            return "Placeholder Text"
