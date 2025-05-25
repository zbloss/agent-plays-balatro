from pydantic_settings import BaseSettings
from pydantic import Field

class Config(BaseSettings):
    llm_api_key: str = Field(..., env="LLM_API_KEY")
    llm_api_base: str = Field(..., env="LLM_API_BASE")
