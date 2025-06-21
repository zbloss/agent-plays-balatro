from autogen_ext.models.ollama import OllamaChatCompletionClient
from balatro_agent.config import Config
from autogen_core.models import ModelFamily

config = Config()
print(f"config: {config}")

base_model = OllamaChatCompletionClient(
    model=config.default_model,
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": False,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
    },
)


if __name__ == "__main__":
    import asyncio
    from autogen_core.models import UserMessage

    async def main():
        result = await base_model.create(
            [UserMessage(content="What is the capital of France?", source="user")]
        )
        print(result)
        await base_model.close()

    asyncio.run(main())
