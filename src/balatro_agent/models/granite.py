from autogen_ext.models.ollama import OllamaChatCompletionClient
from balatro_agent.config import Config
from autogen_core.models import ModelFamily

config = Config(default_model="granite3.2-vision:2b")

granite_model = OllamaChatCompletionClient(
    model=config.default_model,
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
    },
)

if __name__ == "__main__":
    import asyncio
    from autogen_core.models import UserMessage

    async def main():
        result = await granite_model.create(
            [UserMessage(content="What is the capital of France?", source="user")]
        )
        print(result)
        await granite_model.close()

    asyncio.run(main())
