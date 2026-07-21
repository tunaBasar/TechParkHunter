from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "TechPark Hunter"
    DEBUG: bool = True
    DATA_DIR: str = "data"
    DATABASE_URL: str = "techpark_hunter.db"
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3.3"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
