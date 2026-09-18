from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
