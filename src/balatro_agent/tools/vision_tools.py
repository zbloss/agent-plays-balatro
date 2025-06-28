import cv2
import numpy as np
from PIL import Image
import base64
import io
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field
import re
from pathlib import Path
import json
import pyautogui
import pytesseract

from balatro_agent.models.game_models import Card, Joker, Suit, Rank
from balatro_agent.config import Config


class DetectedObject(BaseModel):
    """Represents a detected object in the game screenshot."""
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int] = Field(description="x, y, width, height")
    center: Tuple[int, int]
    text: Optional[str] = None


class BalatroVisionProcessor(BaseModel):
    """Advanced computer vision processor for Balatro game state detection."""
    
    card_templates: Dict[str, Any] = Field(default_factory=dict)
    joker_templates: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self.card_templates = self._load_card_templates()
        self.joker_templates = self._load_joker_templates()
        
    def _load_card_templates(self) -> Dict[str, np.ndarray]:
        """Load card rank and suit templates for matching."""
        # This would load pre-saved templates of card ranks and suits
        # For now, return empty dict - templates would be created from game screenshots
        return {}
    
    def _load_joker_templates(self) -> Dict[str, np.ndarray]:
        """Load joker templates for recognition."""
        return {}
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Take a screenshot of the game window."""
        screenshot = pyautogui.screenshot(region=region)
        return np.array(screenshot)
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR and detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def detect_cards_in_hand(self, image: np.ndarray) -> List[Card]:
        """Detect cards in the player's hand."""
        # This would use computer vision to identify card positions and values
        # For now, return placeholder implementation
        cards = []
        
        # Find card-like rectangular regions
        card_regions = self._find_card_regions(image)
        
        for region in card_regions:
            x, y, w, h = region
            card_image = image[y:y+h, x:x+w]
            
            # Try to identify rank and suit
            rank, suit = self._identify_card(card_image)
            
            if rank and suit:
                card = Card(
                    rank=rank,
                    suit=suit,
                    position=(x + w//2, y + h//2)
                )
                cards.append(card)
        
        return cards
    
    def _find_card_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Find rectangular regions that likely contain cards."""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        card_regions = []
        for contour in contours:
            # Approximate the contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # If we have 4 points, it might be a card
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (cards should be within certain dimensions)
                aspect_ratio = w / h
                if 0.6 <= aspect_ratio <= 0.8 and w > 50 and h > 70:
                    card_regions.append((x, y, w, h))
        
        return card_regions
    
    def _identify_card(self, card_image: np.ndarray) -> Tuple[Optional[Rank], Optional[Suit]]:
        """Identify the rank and suit of a card from its image."""
        # Extract text using OCR
        text = pytesseract.image_to_string(card_image, config='--psm 8 -c tessedit_char_whitelist=0123456789AJQK')
        text = text.strip().upper()
        
        # Try to match rank
        rank = None
        if text in ['A', 'ACE']:
            rank = Rank.ACE
        elif text in ['K', 'KING']:
            rank = Rank.KING
        elif text in ['Q', 'QUEEN']:
            rank = Rank.QUEEN
        elif text in ['J', 'JACK']:
            rank = Rank.JACK
        elif text.isdigit():
            num = int(text)
            if 2 <= num <= 10:
                rank_map = {
                    2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
                    6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE, 10: Rank.TEN
                }
                rank = rank_map.get(num)
        
        # Identify suit by color analysis
        suit = self._identify_suit_by_color(card_image)
        
        return rank, suit
    
    def _identify_suit_by_color(self, card_image: np.ndarray) -> Optional[Suit]:
        """Identify card suit by analyzing color distribution."""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(card_image, cv2.COLOR_RGB2HSV)
        
        # Define color ranges for red and black suits
        red_lower = np.array([0, 50, 50])
        red_upper = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        
        black_lower = np.array([0, 0, 0])
        black_upper = np.array([180, 255, 50])
        black_mask = cv2.inRange(hsv, black_lower, black_upper)
        
        red_pixels = np.sum(red_mask > 0)
        black_pixels = np.sum(black_mask > 0)
        
        # Very basic heuristic - would need more sophisticated analysis
        if red_pixels > black_pixels:
            return Suit.HEARTS  # Could be diamonds too
        else:
            return Suit.SPADES  # Could be clubs too
    
    def detect_jokers(self, image: np.ndarray) -> List[Joker]:
        """Detect jokers in the current view."""
        jokers = []
        
        # Find joker-like regions (typically rectangular with specific styling)
        joker_regions = self._find_joker_regions(image)
        
        for region in joker_regions:
            x, y, w, h = region
            joker_image = image[y:y+h, x:x+w]
            
            # Extract joker name and description
            joker_info = self._extract_joker_info(joker_image)
            
            if joker_info:
                joker = Joker(
                    name=joker_info.get('name', 'Unknown'),
                    description=joker_info.get('description', ''),
                    position=(x + w//2, y + h//2)
                )
                jokers.append(joker)
        
        return jokers
    
    def _find_joker_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Find regions that likely contain jokers."""
        # Placeholder implementation
        return []
    
    def _extract_joker_info(self, joker_image: np.ndarray) -> Optional[Dict[str, str]]:
        """Extract joker name and description from image."""
        # Use OCR to extract text
        text = pytesseract.image_to_string(joker_image)
        
        # Parse the text to extract name and description
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) >= 2:
            return {
                'name': lines[0],
                'description': ' '.join(lines[1:])
            }
        
        return None
    
    def extract_game_stats(self, image: np.ndarray) -> Dict[str, int]:
        """Extract game statistics from the UI."""
        stats = {}
        
        # Define regions where different stats appear
        stat_regions = {
            'money': (10, 10, 100, 30),
            'ante': (10, 50, 100, 30),
            'hands_left': (10, 90, 100, 30),
            'discards_left': (10, 130, 100, 30),
            'score': (10, 170, 200, 30)
        }
        
        for stat_name, (x, y, w, h) in stat_regions.items():
            region_image = image[y:y+h, x:x+w]
            
            # Preprocess for better OCR
            processed = self.preprocess_image(region_image)
            
            # Extract text
            text = pytesseract.image_to_string(processed, config='--psm 8 -c tessedit_char_whitelist=0123456789')
            
            # Extract numbers
            numbers = re.findall(r'\d+', text)
            if numbers:
                stats[stat_name] = int(numbers[0])
        
        return stats
    
    def detect_shop_items(self, image: np.ndarray) -> Dict[str, List]:
        """Detect items available in the shop."""
        shop_items = {
            'jokers': [],
            'cards': [],
            'booster_packs': [],
            'vouchers': []
        }
        
        # This would analyze the shop interface
        # Placeholder implementation
        return shop_items
    
    def is_game_phase(self, image: np.ndarray, phase: str) -> bool:
        """Determine if the game is in a specific phase."""
        # Analyze UI elements to determine current game phase
        # This would look for specific buttons, text, or layouts
        return False
