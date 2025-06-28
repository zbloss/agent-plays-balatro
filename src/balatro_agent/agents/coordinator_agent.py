import asyncio
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from balatro_agent.models.game_models import GameState, Card, Joker, Hand
from balatro_agent.agents.game_state_agent import GameStateAgent
from balatro_agent.agents.strategy_agent import StrategyAgent
from balatro_agent.agents.action_agent import ActionAgent
from balatro_agent.agents.memory_agent import MemoryAgent
from balatro_agent.config import Config


class GamePhase(Enum):
    """Game phases for coordination."""
    INITIALIZATION = "initialization"
    OBSERVATION = "observation"
    STRATEGY = "strategy"
    ACTION = "action"
    MEMORY = "memory"
    ERROR = "error"


class CoordinatorAgent(BaseModel):
    """Master coordinator for the Balatro agent fleet."""
    
    config: Config = Field(default_factory=Config)
    game_state_agent: GameStateAgent = Field(default_factory=GameStateAgent)
    strategy_agent: StrategyAgent = Field(default_factory=StrategyAgent)
    action_agent: ActionAgent = Field(default_factory=ActionAgent)
    memory_agent: MemoryAgent = Field(default_factory=MemoryAgent)
    
    # Coordination state
    current_phase: GamePhase = GamePhase.INITIALIZATION
    game_running: bool = False
    current_game_id: Optional[str] = None
    decision_timeout: float = Field(default=30.0)
    max_retries: int = Field(default=3)
    
    class Config:
        arbitrary_types_allowed = True
    
    async def start_game_session(self) -> bool:
        """Initialize and start a new game session."""
        print("🎮 Starting new Balatro game session...")
        
        try:
            # Initialize memory tracking
            self.current_game_id = self.memory_agent.start_new_game()
            
            # Take initial screenshot and analyze game state
            await self._update_game_state()
            
            # Set up game session
            self.game_running = True
            self.current_phase = GamePhase.OBSERVATION
            
            print(f"✅ Game session started: {self.current_game_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start game session: {e}")
            self.current_phase = GamePhase.ERROR
            return False
    
    async def run_game_loop(self) -> Dict[str, Any]:
        """Main game loop coordinating all agents."""
        if not self.game_running:
            print("❌ No active game session")
            return {"success": False, "error": "No active game session"}
        
        game_result = {
            "success": False,
            "final_ante": 0,
            "final_score": 0,
            "total_decisions": 0,
            "errors": []
        }
        
        try:
            while self.game_running:
                # Main coordination cycle
                cycle_start = time.time()
                
                # Phase 1: Observation - Update game state
                self.current_phase = GamePhase.OBSERVATION
                if not await self._observation_phase():
                    break
                
                # Phase 2: Strategy - Make decisions
                self.current_phase = GamePhase.STRATEGY
                decision = await self._strategy_phase()
                
                if not decision:
                    print("⚠️ No valid decision made")
                    await asyncio.sleep(1)
                    continue
                
                # Phase 3: Action - Execute decisions
                self.current_phase = GamePhase.ACTION
                action_success = await self._action_phase(decision)
                
                # Phase 4: Memory - Record results
                self.current_phase = GamePhase.MEMORY
                await self._memory_phase(decision, action_success)
                
                game_result["total_decisions"] += 1
                
                # Check for game end conditions
                if await self._check_game_end():
                    break
                
                # Rate limiting
                cycle_time = time.time() - cycle_start
                if cycle_time < 2.0:  # Minimum 2 seconds between cycles
                    await asyncio.sleep(2.0 - cycle_time)
        
        except Exception as e:
            print(f"❌ Error in game loop: {e}")
            game_result["errors"].append(str(e))
            self.current_phase = GamePhase.ERROR
        
        finally:
            # End game session
            await self._end_game_session(game_result)
        
        return game_result
    
    async def _observation_phase(self) -> bool:
        """Update game state through observation."""
        try:
            print("👁️ Observing game state...")
            
            # Update game state from screenshot
            game_state = await self.game_state_agent.update_game_state_from_screenshot()
            
            print(f"📊 {self.game_state_agent.get_state_summary()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Observation phase failed: {e}")
            return False
    
    async def _strategy_phase(self) -> Optional[Dict[str, Any]]:
        """Make strategic decisions based on current game state."""
        try:
            print("🧠 Making strategic decision...")
            
            game_state = self.game_state_agent.game_state
            
            # Get memory-based recommendations
            memory_recommendation = self.memory_agent.get_strategy_recommendation(game_state)
            print(f"🧩 Memory recommendation: {memory_recommendation}")
            
            # Make decision based on game phase
            if game_state.game_phase == "select":
                return await self._decide_play_or_discard(game_state)
            
            elif game_state.game_phase == "shop":
                return await self._decide_shop_action(game_state)
            
            else:
                print(f"⚠️ Unknown game phase: {game_state.game_phase}")
                return {"action": "wait", "reason": "Unknown phase"}
        
        except Exception as e:
            print(f"❌ Strategy phase failed: {e}")
            return None
    
    async def _decide_play_or_discard(self, game_state: GameState) -> Dict[str, Any]:
        """Decide whether to play a hand or discard cards."""
        decision = self.strategy_agent.should_play_hand(game_state)
        
        print(f"🎯 Decision: {decision['action']} - {decision['reason']}")
        
        return decision
    
    async def _decide_shop_action(self, game_state: GameState) -> Dict[str, Any]:
        """Decide what to do in the shop."""
        # Get shop recommendations
        shop_recommendations = self.strategy_agent.evaluate_shop_purchases(game_state)
        
        # Get memory-based joker recommendation
        if game_state.shop.jokers:
            memory_joker = self.memory_agent.get_joker_recommendation(
                game_state.shop.jokers, game_state
            )
            
            if memory_joker and shop_recommendations:
                # Prefer memory recommendation if it's in the top recommendations
                for rec in shop_recommendations[:3]:  # Top 3
                    if rec["item"].name == memory_joker.name:
                        return {
                            "action": "buy_joker",
                            "item": memory_joker,
                            "reason": f"Memory recommends {memory_joker.name}"
                        }
        
        # Use strategy agent's recommendation
        if shop_recommendations:
            best_rec = shop_recommendations[0]
            return {
                "action": f"buy_{best_rec['type']}",
                "item": best_rec["item"],
                "reason": f"Best ROI: {best_rec['roi']:.2f}"
            }
        
        # If no good purchases, skip or reroll based on money
        if game_state.player_stats.money >= game_state.shop.reroll_cost * 2:
            return {"action": "reroll", "reason": "Rerolling for better options"}
        else:
            return {"action": "skip", "reason": "No good purchases, saving money"}
    
    async def _action_phase(self, decision: Dict[str, Any]) -> bool:
        """Execute the decided action."""
        try:
            action_type = decision["action"]
            print(f"🎬 Executing action: {action_type}")
            
            if action_type == "play":
                cards = decision.get("cards", [])
                return await self.action_agent.execute_play_action(cards)
            
            elif action_type == "discard":
                cards = decision.get("cards", [])
                return await self.action_agent.execute_discard_action(cards)
            
            elif action_type.startswith("buy_"):
                item = decision.get("item")
                if item and hasattr(item, 'position'):
                    return await self.action_agent.execute_shop_action(
                        action_type, position=item.position
                    )
            
            elif action_type in ["skip", "reroll"]:
                return await self.action_agent.execute_shop_action(action_type)
            
            elif action_type == "wait":
                await asyncio.sleep(1)
                return True
            
            else:
                print(f"⚠️ Unknown action type: {action_type}")
                return False
        
        except Exception as e:
            print(f"❌ Action phase failed: {e}")
            return False
    
    async def _memory_phase(self, decision: Dict[str, Any], action_success: bool):
        """Record decision and outcome in memory."""
        try:
            game_state = self.game_state_agent.game_state
            
            # Record the decision
            context = {
                "ante": game_state.player_stats.ante,
                "money": game_state.player_stats.money,
                "hands_left": game_state.player_stats.hands_left,
                "discards_left": game_state.player_stats.discards_left,
                "game_phase": game_state.game_phase
            }
            
            outcome = {
                "success": action_success,
                "timestamp": time.time()
            }
            
            self.memory_agent.record_decision(
                decision_type="gameplay_decision",
                context=context,
                action=decision,
                outcome=outcome
            )
            
            # Record specific actions
            if decision["action"] == "play" and action_success:
                # This would need the actual hand result from the game
                # For now, we'll simulate it
                cards = decision.get("cards", [])
                if cards:
                    hand_result = self.strategy_agent.hand_evaluator.calculate_hand_score(
                        cards, game_state.active_jokers
                    )
                    self.memory_agent.record_hand_played(hand_result, game_state, True)
            
            elif decision["action"].startswith("buy_") and action_success:
                item = decision.get("item")
                if item:
                    item_type = "joker" if hasattr(item, 'description') else "card"
                    self.memory_agent.record_shop_purchase(
                        item_type=item_type,
                        item_name=item.name if hasattr(item, 'name') else str(item),
                        cost=getattr(item, 'cost', 0),
                        ante=game_state.player_stats.ante
                    )
        
        except Exception as e:
            print(f"❌ Memory phase failed: {e}")
    
    async def _check_game_end(self) -> bool:
        """Check if the game has ended."""
        game_state = self.game_state_agent.game_state
        
        # Check for victory
        if game_state.has_winning_score():
            print("🎉 Victory! Target score reached!")
            return True
        
        # Check for defeat (no hands/discards left and score insufficient)
        if (game_state.player_stats.hands_left <= 0 and 
            game_state.player_stats.discards_left <= 0 and
            not game_state.has_winning_score()):
            print("💀 Defeat! No more actions available!")
            return True
        
        # Check for manual stop condition (could be implemented)
        return False
    
    async def _update_game_state(self):
        """Update the game state."""
        await self.game_state_agent.update_game_state_from_screenshot()
    
    async def _end_game_session(self, game_result: Dict[str, Any]):
        """End the current game session."""
        try:
            game_state = self.game_state_agent.game_state
            
            # Update game result
            game_result["final_ante"] = game_state.player_stats.ante
            game_result["final_score"] = game_state.player_stats.current_score
            game_result["success"] = game_state.has_winning_score()
            
            # End memory tracking
            self.memory_agent.end_current_game(
                final_ante=game_result["final_ante"],
                final_score=game_result["final_score"],
                success=game_result["success"]
            )
            
            # Save performance stats
            self.memory_agent.save_performance_stats()
            
            # Reset state
            self.game_running = False
            self.current_game_id = None
            self.current_phase = GamePhase.INITIALIZATION
            
            print(f"🏁 Game session ended: {game_result}")
            
        except Exception as e:
            print(f"❌ Error ending game session: {e}")
    
    async def calibrate_system(self) -> Dict[str, Any]:
        """Calibrate the system for the current game setup."""
        print("🔧 Starting system calibration...")
        
        try:
            # Calibrate UI positions
            ui_positions = await self.action_agent.calibrate_ui_positions()
            
            # Take test screenshot
            screenshot_path = self.action_agent.take_screenshot_for_analysis()
            
            # Test game state detection
            await self._update_game_state()
            
            calibration_result = {
                "ui_positions": ui_positions,
                "screenshot_path": screenshot_path,
                "game_state_detected": bool(self.game_state_agent.game_state),
                "memory_summary": self.memory_agent.get_memory_summary()
            }
            
            print(f"✅ Calibration complete: {calibration_result}")
            return calibration_result
            
        except Exception as e:
            print(f"❌ Calibration failed: {e}")
            return {"error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "current_phase": self.current_phase.value,
            "game_running": self.game_running,
            "current_game_id": self.current_game_id,
            "game_state_summary": self.game_state_agent.get_state_summary(),
            "memory_summary": self.memory_agent.get_memory_summary()
        }
