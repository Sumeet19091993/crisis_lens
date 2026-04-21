from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CrisisLens API"
    APP_ENV: str = "dev"
    APP_PORT: int = 8000

    DATABASE_URL: str = "postgresql+psycopg://crisislens:crisislens@localhost:5432/crisislens"
    REDIS_URL: str = "redis://localhost:6379/0"

    REDIS_STREAM_REPORTS: str = "reports:new"
    REDIS_STREAM_GROUP: str = "dispatchers"
    REDIS_STREAM_CONSUMER: str = "worker-1"

    JWT_SECRET: str = "change_me_in_production"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 14
    TOKEN_REVOKE_PREFIX: str = "revoked"

    @property
    def database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL


settings = Settings()
