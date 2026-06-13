from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db/jobtracker_dev"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    demo_email: str = "demo@jobtracker.dev"
    demo_password: str = "DemoPass123!"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
