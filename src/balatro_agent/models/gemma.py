from autogen_ext.models.ollama import OllamaChatCompletionClient
from balatro_agent.config import Config
from autogen_core.models import ModelFamily


config = Config(default_model="gemma3:4b-it-qat")

gemma_model = OllamaChatCompletionClient(
    model=config.default_model,
    model_info={
        "json_output": False,
        "function_calling": False,
        "vision": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": False,
    },
)

if __name__ == "__main__":
    import asyncio
    from io import BytesIO

    import requests
    from autogen_agentchat.messages import MultiModalMessage
    from autogen_core import Image as AGImage
    from PIL import Image
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.ui import Console

    pil_image = Image.open(
        BytesIO(
            requests.get(
                "https://media.cnn.com/api/v1/images/stellar/prod/210602230802-01-puppy-social-skills-wellness-sci.jpg?q=w_1600,h_1453,x_0,y_0,c_fill"
            ).content
        )
    )
    img = AGImage(pil_image)
    print(img)
    multi_modal_message = MultiModalMessage(
        content=["Can you describe the content of this image?", img], source="User"
    )

    agent = AssistantAgent(
        name="image_assistant",
        model_client=gemma_model,
        description="An agent that analyzes images and provides descriptions.",
        reflect_on_tool_use=True,
        system_message="Given an image, provide a description of the content.",
    )

    async def main(multi_modal_message):
        result = await Console(agent.run_stream(task=multi_modal_message))
        await gemma_model.close()

    asyncio.run(main(multi_modal_message))
