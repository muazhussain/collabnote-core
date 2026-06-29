from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Application name.
        version: Application version.
        database_url: PostgreSQL connection URL.
        redis_url: Redis connection URL.
        mongodb_url: MongoDB connection URL.
        mongodb_db_name: MongoDB database name.
        secret_key: Secret key for JWT signing.
        algorithm: JWT signing algorithm.
        access_token_expire_minutes: JWT token expiry duration in minutes.
    """

    app_name: str = "Collabnote"
    version: str = "1.0.0"
    database_url: str
    redis_url: str
    mongodb_url: str
    mongodb_db_name: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()  # type: ignore[call-arg]
