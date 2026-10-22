
# Reads settings from environment variables (loaded from .env) once. The rest of the code imports
# `settings` instead of reading os.environ in many places.

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./articulate_dev.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    CORS_ALLOWED_ORIGIN: str = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")


settings = Settings()

if not settings.JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Copy .env.example to .env and set a long random value."
    )
