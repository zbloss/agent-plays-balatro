from smolagents import CodeAgent, LiteLLMModel
from balatro_agent.tools.mouse import MouseTool
from balatro_agent.config import Config


config = Config()


if __name__ == "__main__":
    model = LiteLLMModel(
        model_id="gemini/gemini-2.0-flash-lite",
        api_key=config.llm_api_key,
        api_base=config.llm_api_base,
    )

    agent = CodeAgent(
        model=model,
        tools=[MouseTool()],
        name="mouse_agent",
        description="An agent that can control the mouse and take screenshots.",
        max_steps=5,
    )
    agent.run("double click at (100, 200).")
