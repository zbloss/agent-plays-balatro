import asyncio
import json
import pickle
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from collections import defaultdict, deque

from balatro_agent.models.game_models import GameState, Hand, Joker, Card, HandType


class GameMemory(BaseModel):
    """Stores information about a single game session."""
    
    game_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    final_ante: int = 0
    final_score: int = 0
    success: bool = False
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    jokers_used: List[str] = Field(default_factory=list)
    hands_played: List[Dict[str, Any]] = Field(default_factory=list)
    shop_purchases: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class StrategyPattern(BaseModel):
    """Represents a learned strategy pattern."""
    
    pattern_id: str
    name: str
    description: str
    conditions: Dict[str, Any]  # When to use this pattern
    actions: List[Dict[str, Any]]  # What actions to take
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None


class MemoryAgent(BaseModel):
    """Agent responsible for learning and memory management."""
    
    memory_dir: Path = Field(default=Path("./memory"))
    max_games_in_memory: int = Field(default=1000)
    game_memories: deque = Field(default_factory=lambda: deque(maxlen=1000))
    strategy_patterns: Dict[str, StrategyPattern] = Field(default_factory=dict)
    joker_performance: Dict[str, Dict[str, float]] = Field(default_factory=lambda: defaultdict(dict))
    hand_type_performance: Dict[HandType, Dict[str, float]] = Field(default_factory=lambda: defaultdict(dict))
    current_game: Optional[GameMemory] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self.memory_dir.mkdir(exist_ok=True)
        self.load_persistent_memory()
    
    def start_new_game(self, game_id: str = None) -> str:
        """Start tracking a new game."""
        if game_id is None:
            game_id = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_game = GameMemory(
            game_id=game_id,
            start_time=datetime.now()
        )
        
        print(f"Started tracking game: {game_id}")
        return game_id
    
    def end_current_game(self, final_ante: int, final_score: int, success: bool):
        """End the current game and store results."""
        if not self.current_game:
            print("No current game to end")
            return
        
        self.current_game.end_time = datetime.now()
        self.current_game.final_ante = final_ante
        self.current_game.final_score = final_score
        self.current_game.success = success
        
        # Add to memory
        self.game_memories.append(self.current_game)
        
        # Update performance statistics
        self._update_performance_stats()
        
        # Save to persistent storage
        self.save_game_memory(self.current_game)
        
        print(f"Game {self.current_game.game_id} ended. Success: {success}, Final Ante: {final_ante}")
        self.current_game = None
    
    def record_decision(self, decision_type: str, context: Dict[str, Any], 
                       action: Dict[str, Any], outcome: Dict[str, Any]):
        """Record a decision made during the game."""
        if not self.current_game:
            return
        
        decision = {
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "context": context,
            "action": action,
            "outcome": outcome
        }
        
        self.current_game.decisions.append(decision)
    
    def record_hand_played(self, hand: Hand, game_state: GameState, success: bool):
        """Record information about a hand that was played."""
        if not self.current_game:
            return
        
        hand_record = {
            "timestamp": datetime.now().isoformat(),
            "hand_type": hand.hand_type.value,
            "score": hand.final_score,
            "cards": [{"rank": c.rank.value, "suit": c.suit.value} for c in hand.cards],
            "ante": game_state.player_stats.ante,
            "hands_left": game_state.player_stats.hands_left,
            "success": success
        }
        
        self.current_game.hands_played.append(hand_record)
    
    def record_shop_purchase(self, item_type: str, item_name: str, cost: int, 
                           ante: int, outcome_score: float = None):
        """Record a shop purchase and its effectiveness."""
        if not self.current_game:
            return
        
        purchase = {
            "timestamp": datetime.now().isoformat(),
            "type": item_type,
            "name": item_name,
            "cost": cost,
            "ante": ante,
            "outcome_score": outcome_score
        }
        
        self.current_game.shop_purchases.append(purchase)
        
        if item_type == "joker":
            if item_name not in self.current_game.jokers_used:
                self.current_game.jokers_used.append(item_name)
    
    def get_joker_recommendation(self, available_jokers: List[Joker], 
                               game_state: GameState) -> Optional[Joker]:
        """Recommend a joker based on historical performance."""
        if not available_jokers:
            return None
        
        best_joker = None
        best_score = -1
        
        for joker in available_jokers:
            performance = self.joker_performance.get(joker.name, {})
            
            # Calculate composite score based on various factors
            win_rate = performance.get('win_rate', 0.5)  # Default neutral
            avg_score_boost = performance.get('avg_score_boost', 0)
            usage_count = performance.get('usage_count', 0)
            
            # Bonus for rarity
            rarity_bonus = {"Common": 0, "Uncommon": 0.1, "Rare": 0.2, "Legendary": 0.3}
            bonus = rarity_bonus.get(joker.rarity, 0)
            
            # Penalty for unknown jokers to encourage exploration
            exploration_bonus = 0.1 if usage_count < 5 else 0
            
            composite_score = (win_rate + bonus + exploration_bonus) * (1 + avg_score_boost / 1000)
            
            if composite_score > best_score:
                best_score = composite_score
                best_joker = joker
        
        return best_joker
    
    def get_strategy_recommendation(self, game_state: GameState) -> Dict[str, Any]:
        """Get strategy recommendations based on historical data."""
        ante = game_state.player_stats.ante
        money = game_state.player_stats.money
        current_score = game_state.player_stats.current_score
        target_score = game_state.player_stats.target_score
        
        # Find similar game situations
        similar_situations = self._find_similar_situations(game_state)
        
        if not similar_situations:
            return {"strategy": "default", "confidence": 0.3}
        
        # Analyze successful strategies in similar situations
        successful_strategies = [s for s in similar_situations if s.get('success', False)]
        
        if successful_strategies:
            # Extract common patterns from successful games
            common_actions = self._extract_common_patterns(successful_strategies)
            return {
                "strategy": "learned",
                "actions": common_actions,
                "confidence": len(successful_strategies) / len(similar_situations)
            }
        
        return {"strategy": "exploration", "confidence": 0.4}
    
    def _find_similar_situations(self, current_state: GameState) -> List[Dict[str, Any]]:
        """Find historically similar game situations."""
        similar = []
        
        for game in self.game_memories:
            for decision in game.decisions:
                if decision.get('type') == 'strategy_decision':
                    context = decision.get('context', {})
                    
                    # Check similarity based on ante, money, and score progress
                    ante_diff = abs(context.get('ante', 0) - current_state.player_stats.ante)
                    money_ratio = (context.get('money', 1) + 1) / (current_state.player_stats.money + 1)
                    
                    if ante_diff <= 1 and 0.5 <= money_ratio <= 2.0:
                        similar.append({
                            'context': context,
                            'action': decision.get('action'),
                            'outcome': decision.get('outcome'),
                            'success': game.success
                        })
        
        return similar
    
    def _extract_common_patterns(self, situations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common action patterns from successful situations."""
        action_counts = defaultdict(int)
        
        for situation in situations:
            action = situation.get('action', {})
            action_type = action.get('type', 'unknown')
            action_counts[action_type] += 1
        
        # Return most common actions
        common_actions = []
        for action_type, count in action_counts.items():
            if count >= len(situations) * 0.6:  # Used in 60%+ of cases
                common_actions.append({
                    'type': action_type,
                    'frequency': count / len(situations)
                })
        
        return common_actions
    
    def _update_performance_stats(self):
        """Update performance statistics after a game ends."""
        if not self.current_game:
            return
        
        # Update joker performance
        for joker_name in self.current_game.jokers_used:
            if joker_name not in self.joker_performance:
                self.joker_performance[joker_name] = {
                    'win_rate': 0.0,
                    'usage_count': 0,
                    'total_score': 0,
                    'avg_score_boost': 0
                }
            
            stats = self.joker_performance[joker_name]
            stats['usage_count'] += 1
            stats['total_score'] += self.current_game.final_score
            
            # Update win rate
            if self.current_game.success:
                old_wins = stats['win_rate'] * (stats['usage_count'] - 1)
                stats['win_rate'] = (old_wins + 1) / stats['usage_count']
            else:
                old_wins = stats['win_rate'] * (stats['usage_count'] - 1)
                stats['win_rate'] = old_wins / stats['usage_count']
            
            # Update average score boost (simplified calculation)
            avg_game_score = 1000  # Baseline assumption
            stats['avg_score_boost'] = stats['total_score'] / stats['usage_count'] - avg_game_score
        
        # Update hand type performance
        for hand_record in self.current_game.hands_played:
            hand_type = HandType(hand_record['hand_type'])
            
            if hand_type not in self.hand_type_performance:
                self.hand_type_performance[hand_type] = {
                    'usage_count': 0,
                    'success_rate': 0.0,
                    'avg_score': 0.0
                }
            
            stats = self.hand_type_performance[hand_type]
            stats['usage_count'] += 1
            
            # Update success rate
            if hand_record['success']:
                old_successes = stats['success_rate'] * (stats['usage_count'] - 1)
                stats['success_rate'] = (old_successes + 1) / stats['usage_count']
            else:
                old_successes = stats['success_rate'] * (stats['usage_count'] - 1)
                stats['success_rate'] = old_successes / stats['usage_count']
            
            # Update average score
            old_total = stats['avg_score'] * (stats['usage_count'] - 1)
            stats['avg_score'] = (old_total + hand_record['score']) / stats['usage_count']
    
    def save_game_memory(self, game: GameMemory):
        """Save a game memory to persistent storage."""
        filename = self.memory_dir / f"{game.game_id}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(game.model_dump(), f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save game memory: {e}")
    
    def load_persistent_memory(self):
        """Load persistent memory from disk."""
        try:
            # Load individual game memories
            for json_file in self.memory_dir.glob("game_*.json"):
                with open(json_file) as f:
                    game_data = json.load(f)
                    game = GameMemory.model_validate(game_data)
                    if len(self.game_memories) < self.max_games_in_memory:
                        self.game_memories.append(game)
            
            # Load performance statistics
            stats_file = self.memory_dir / "performance_stats.json"
            if stats_file.exists():
                with open(stats_file) as f:
                    stats = json.load(f)
                    self.joker_performance = defaultdict(dict, stats.get('joker_performance', {}))
                    
                    # Convert hand type keys back to enums
                    hand_perf = {}
                    for hand_str, perf in stats.get('hand_type_performance', {}).items():
                        try:
                            hand_type = HandType(hand_str)
                            hand_perf[hand_type] = perf
                        except ValueError:
                            continue
                    self.hand_type_performance = defaultdict(dict, hand_perf)
            
            print(f"Loaded {len(self.game_memories)} game memories")
            
        except Exception as e:
            print(f"Failed to load persistent memory: {e}")
    
    def save_performance_stats(self):
        """Save performance statistics to disk."""
        stats_file = self.memory_dir / "performance_stats.json"
        
        try:
            # Convert hand type keys to strings for JSON serialization
            hand_perf = {}
            for hand_type, perf in self.hand_type_performance.items():
                hand_perf[hand_type.value] = perf
            
            stats = {
                'joker_performance': dict(self.joker_performance),
                'hand_type_performance': hand_perf
            }
            
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save performance stats: {e}")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of the current memory state."""
        successful_games = sum(1 for game in self.game_memories if game.success)
        total_games = len(self.game_memories)
        
        return {
            "total_games": total_games,
            "successful_games": successful_games,
            "win_rate": successful_games / total_games if total_games > 0 else 0,
            "tracked_jokers": len(self.joker_performance),
            "strategy_patterns": len(self.strategy_patterns),
            "memory_usage": f"{len(self.game_memories)}/{self.max_games_in_memory}"
        }
