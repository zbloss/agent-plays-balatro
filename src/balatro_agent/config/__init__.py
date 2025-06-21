from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    llm_api_key: str = Field("None", env="LLM_API_KEY")
    llm_api_base: str = Field("http://localhost:11434/v1", env="LLM_API_BASE")
    default_model: str = Field("qwen3:4b", env="DEFAULT_MODEL")
    balatro_wiki_url: str = Field(
        "https://balatro.fandom.com/wiki/Balatro", env="BALATRO_WIKI_URL"
    )
