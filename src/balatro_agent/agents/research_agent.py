from smolagents import CodeAgent, LiteLLMModel, WebSearchTool
from balatro_agent.config import Config
from smolagents.vision_web_browser import (
    search_item_ctrl_f,
    go_back,
    close_popups,
    initialize_driver,
    save_screenshot,
    helium_instructions,
    tool
)
import os
from balatro_agent.prompts import BALATRO_WIKI

config = Config()

global driver
driver = initialize_driver()


@tool
def save_markdown(markdown: str, filename: str) -> str:
    """
    Save the provided markdown content to a file at
    filename.

    Args:
        markdown (str): The markdown content to save.
        filename (str): The name of the file to save the content to, ending in `.md`.
        
    Returns:
        str: A message indicating the file has been saved.
    """

    if not filename.endswith(".md"):
        filename += ".md"

    current_directory: str = os.path.dirname(os.path.abspath(__file__))
    research_directory: str = os.path.join(current_directory, "../", "research")
    filepath: str = os.path.join(research_directory, filename)
    with open(filepath, "w") as f:
        f.write(markdown)
    return f"Markdown content saved to {filepath}."




if __name__ == "__main__":
    model = LiteLLMModel(
        model_id="gemini/gemini-2.0-flash-lite",
        api_key=config.llm_api_key,
        api_base=config.llm_api_base,
    )
    
    agent = CodeAgent(
        tools=[WebSearchTool(), go_back, close_popups, search_item_ctrl_f, save_markdown],
        model=model,
        additional_authorized_imports=["helium"],
        step_callbacks=[save_screenshot],
        max_steps=20,
        verbosity_level=2,
    )

    # Run the agent with the provided prompt
    agent.python_executor("from helium import *")
    agent.run(BALATRO_WIKI + helium_instructions)
