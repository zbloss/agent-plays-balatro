from agent_plays_balatro.agents.core_observer_agent import CoreObserverAgent
# Context is used by CoreObserverAgent.execute, GameStateAgent might pass an empty one.
# AgentOutput is returned by CoreObserverAgent.execute
from agent_plays_balatro.agents.core_observer_agent import Context, AgentOutput
from agent_plays_balatro.models import GameState

class GameStateAgent:
    def __init__(self, core_observer_config: dict = None):
        """
        Initializes the GameStateAgent.
        It sets up the CoreObserverAgent which is responsible for the actual observation.

        Args:
            core_observer_config (dict, optional): Configuration for the CoreObserverAgent.
        """
        # CoreObserverAgent now handles its own sub-processors/tools like
        # ImageProcessingService, CardRecognitionAgent, JokerRecognitionAgent.
        self.observer = CoreObserverAgent(config=core_observer_config)

    def extract_current_game_state(self) -> GameState | None: # Return type can be None if error
        """
        Extracts the current game state using the CoreObserverAgent.

        Returns:
            GameState: The extracted game state, or None if an error occurred.
        """
        print("GameStateAgent: Requesting game state from CoreObserverAgent...")
        # Create a default/empty context if CoreObserverAgent expects one
        # and GameStateAgent doesn't have specific context to pass.
        # Based on CoreObserverAgent's signature: execute(self, context: Context = None)
        execution_context = Context() # Using the placeholder Context

        observer_output: AgentOutput = self.observer.execute(context=execution_context)

        if observer_output.error:
            print(f"GameStateAgent: CoreObserverAgent returned an error: {observer_output.error}")
            return None

        if observer_output.data and isinstance(observer_output.data, GameState):
            print("GameStateAgent: GameState successfully extracted by CoreObserverAgent.")
            return observer_output.data
        else:
            print(f"GameStateAgent: CoreObserverAgent did not return valid GameState data. Data type: {type(observer_output.data)}")
            return None
