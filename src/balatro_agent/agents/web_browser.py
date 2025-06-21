import asyncio
from autogen_agentchat.ui import Console
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from balatro_agent.models.qwen_vl import qwen_vl_model
from balatro_agent.config import Config

config = Config()

web_surfer_agent = MultimodalWebSurfer(
    name="MultimodalWebSurfer",
    model_client=qwen_vl_model,
    headless=False,
    downloads_folder="./downloads",
    debug_dir="./debug",
    animate_actions=True,
    # to_save_screenshots=True,
    # use_ocr=True,
)

# Define a team
agent_team = RoundRobinGroupChat([web_surfer_agent], max_turns=10)


if __name__ == "__main__":

    async def main() -> None:
        # Run the team and stream messages to the console
        await Console(
            agent_team.run_stream(
                task=f"Use the visit_url tool to navigate to {config.balatro_wiki_url}."
            )
        )
        # Close the browser controlled by the agent
        await web_surfer_agent.close()

    asyncio.run(main())
