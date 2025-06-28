import asyncio
import time
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
import pyautogui

from balatro_agent.models.game_models import Card, Joker, GameState
from balatro_agent.tools.vlm_vision_processor import VLMVisionProcessor


class ActionAgent(BaseModel):
    """Agent responsible for executing actions in the Balatro game."""
    
    vision_processor: VLMVisionProcessor = Field(default_factory=VLMVisionProcessor)
    click_delay: float = Field(default=0.5, description="Delay between clicks in seconds")
    action_timeout: float = Field(default=5.0, description="Timeout for actions in seconds")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = self.click_delay
    
    async def click_card(self, card: Card) -> bool:
        """Click on a specific card."""
        if not card.position:
            print(f"Card {card.rank.value} of {card.suit.value} has no position")
            return False
        
        try:
            x, y = card.position
            pyautogui.click(x, y)
            await asyncio.sleep(self.click_delay)
            print(f"Clicked card {card.rank.value} of {card.suit.value} at ({x}, {y})")
            return True
        except Exception as e:
            print(f"Failed to click card: {e}")
            return False
    
    async def click_joker(self, joker: Joker) -> bool:
        """Click on a specific joker."""
        if not joker.position:
            print(f"Joker {joker.name} has no position")
            return False
        
        try:
            x, y = joker.position
            pyautogui.click(x, y)
            await asyncio.sleep(self.click_delay)
            print(f"Clicked joker {joker.name} at ({x}, {y})")
            return True
        except Exception as e:
            print(f"Failed to click joker: {e}")
            return False
    
    async def select_cards(self, cards: List[Card]) -> bool:
        """Select multiple cards for playing."""
        print(f"Selecting {len(cards)} cards for play")
        
        success_count = 0
        for card in cards:
            if await self.click_card(card):
                success_count += 1
            await asyncio.sleep(0.1)  # Small delay between card selections
        
        return success_count == len(cards)
    
    async def play_selected_hand(self) -> bool:
        """Click the play button to play the selected hand."""
        try:
            # Look for the play button (would need to be calibrated for actual game)
            play_button_pos = self._find_ui_element("play_button")
            
            if play_button_pos:
                pyautogui.click(play_button_pos)
                await asyncio.sleep(self.click_delay)
                print("Clicked play button")
                return True
            else:
                print("Could not find play button")
                return False
                
        except Exception as e:
            print(f"Failed to play hand: {e}")
            return False
    
    async def discard_cards(self, cards: List[Card]) -> bool:
        """Discard selected cards."""
        print(f"Discarding {len(cards)} cards")
        
        # First select the cards to discard
        if not await self.select_cards(cards):
            return False
        
        # Then click the discard button
        try:
            discard_button_pos = self._find_ui_element("discard_button")
            
            if discard_button_pos:
                pyautogui.click(discard_button_pos)
                await asyncio.sleep(self.click_delay)
                print("Clicked discard button")
                return True
            else:
                print("Could not find discard button")
                return False
                
        except Exception as e:
            print(f"Failed to discard cards: {e}")
            return False
    
    async def buy_shop_item(self, item_position: Tuple[int, int], item_type: str) -> bool:
        """Buy an item from the shop."""
        try:
            pyautogui.click(item_position)
            await asyncio.sleep(self.click_delay)
            print(f"Clicked on {item_type} at position {item_position}")
            
            # Look for and click buy/confirm button
            buy_button_pos = self._find_ui_element("buy_button")
            if buy_button_pos:
                pyautogui.click(buy_button_pos)
                await asyncio.sleep(self.click_delay)
                print("Confirmed purchase")
                return True
            else:
                print("Could not find buy button")
                return False
                
        except Exception as e:
            print(f"Failed to buy {item_type}: {e}")
            return False
    
    async def skip_shop(self) -> bool:
        """Skip the shop phase."""
        try:
            skip_button_pos = self._find_ui_element("skip_button")
            
            if skip_button_pos:
                pyautogui.click(skip_button_pos)
                await asyncio.sleep(self.click_delay)
                print("Skipped shop")
                return True
            else:
                print("Could not find skip button")
                return False
                
        except Exception as e:
            print(f"Failed to skip shop: {e}")
            return False
    
    async def reroll_shop(self) -> bool:
        """Reroll the shop items."""
        try:
            reroll_button_pos = self._find_ui_element("reroll_button")
            
            if reroll_button_pos:
                pyautogui.click(reroll_button_pos)
                await asyncio.sleep(self.click_delay)
                print("Rerolled shop")
                return True
            else:
                print("Could not find reroll button")
                return False
                
        except Exception as e:
            print(f"Failed to reroll shop: {e}")
            return False
    
    def _find_ui_element(self, element_name: str) -> Optional[Tuple[int, int]]:
        """Find UI elements by name."""
        # This would be implemented with template matching or OCR
        # For now, return hardcoded positions (would need calibration)
        
        ui_positions = {
            "play_button": (960, 800),  # Center bottom area
            "discard_button": (860, 800),  # Left of play button
            "skip_button": (1200, 700),  # Right side
            "reroll_button": (800, 700),  # Shop reroll
            "buy_button": (960, 600),  # Purchase confirmation
        }
        
        return ui_positions.get(element_name)
    
    async def wait_for_game_state(self, expected_phase: str, timeout: float = None) -> bool:
        """Wait for the game to reach a specific state."""
        if timeout is None:
            timeout = self.action_timeout
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            screenshot = self.vision_processor.take_screenshot()
            
            current_phase = await self.vision_processor.identify_game_phase(screenshot)
            if current_phase == expected_phase:
                print(f"Game reached {expected_phase} phase")
                return True
            
            await asyncio.sleep(0.5)
        
        print(f"Timeout waiting for {expected_phase} phase")
        return False
    
    async def execute_play_action(self, cards: List[Card]) -> bool:
        """Execute a complete play action."""
        print(f"Executing play action with {len(cards)} cards")
        
        # Select cards
        if not await self.select_cards(cards):
            print("Failed to select cards")
            return False
        
        # Play the hand
        if not await self.play_selected_hand():
            print("Failed to play hand")
            return False
        
        # Wait for the play to complete
        if not await self.wait_for_game_state("select"):
            print("Play action may not have completed properly")
            return False
        
        print("Play action completed successfully")
        return True
    
    async def execute_discard_action(self, cards: List[Card]) -> bool:
        """Execute a complete discard action."""
        print(f"Executing discard action with {len(cards)} cards")
        
        # Discard cards
        if not await self.discard_cards(cards):
            print("Failed to discard cards")
            return False
        
        # Wait for discard to complete
        if not await self.wait_for_game_state("select"):
            print("Discard action may not have completed properly")
            return False
        
        print("Discard action completed successfully")
        return True
    
    async def execute_shop_action(self, action_type: str, **kwargs) -> bool:
        """Execute shop-related actions."""
        print(f"Executing shop action: {action_type}")
        
        if action_type == "buy_joker":
            joker_position = kwargs.get("position")
            return await self.buy_shop_item(joker_position, "joker")
        
        elif action_type == "buy_card":
            card_position = kwargs.get("position")
            return await self.buy_shop_item(card_position, "card")
        
        elif action_type == "reroll":
            return await self.reroll_shop()
        
        elif action_type == "skip":
            return await self.skip_shop()
        
        else:
            print(f"Unknown shop action: {action_type}")
            return False
    
    def take_screenshot_for_analysis(self) -> str:
        """Take a screenshot and save it for analysis."""
        timestamp = int(time.time())
        filename = f"game_screenshot_{timestamp}.png"
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            print(f"Screenshot saved as {filename}")
            return filename
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return ""
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position for calibration."""
        return pyautogui.position()
    
    async def calibrate_ui_positions(self) -> Dict[str, Tuple[int, int]]:
        """Interactive calibration of UI element positions."""
        print("Starting UI calibration...")
        print("Move mouse to each UI element and press Enter")
        
        elements = [
            "play_button",
            "discard_button", 
            "skip_button",
            "reroll_button"
        ]
        
        positions = {}
        
        for element in elements:
            print(f"Move mouse to {element} and press Enter...")
            input()  # Wait for user input
            positions[element] = self.get_mouse_position()
            print(f"{element} position: {positions[element]}")
        
        return positions
