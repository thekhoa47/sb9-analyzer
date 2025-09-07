from pydantic import BaseModel
from pathlib import Path
import os
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", "8000"))
    ENV: str = os.getenv("ENV", "dev")

    MAPBOX_TOKEN: str = os.getenv("MAPBOX_TOKEN")
    APP_BASE_URL: str = os.getenv("APP_BASE_URL")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY")
    R2_BUCKET: str = os.getenv("R2_BUCKET")
    R2_S3_ENDPOINT: str = os.getenv("R2_S3_ENDPOINT")
    R2_PUBLIC_BASE: str = os.getenv("R2_PUBLIC_BASE")
    R2_ENDPOINT_URL: str = os.getenv("R2_ENDPOINT_URL") or (
        f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else None
    )
    SB9_MODEL_PATH: str = os.getenv("SB9_MODEL_PATH")
    R2_MODEL_BUCKET: str = os.getenv("R2_MODEL_BUCKET")
    R2_MODEL_KEY: str = os.getenv("R2_MODEL_KEY")
    MODEL_CACHE_DIR: str = Path(os.getenv("MODEL_CACHE_DIR"))

    RESO_BASE_URL: str = os.getenv("RESO_BASE_URL")
    RESO_BEARER_TOKEN: str = os.getenv("RESO_BEARER_TOKEN")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    TWILIO_SID: str = os.getenv("TWILIO_SID")
    TWILIO_TOKEN: str = os.getenv("TWILIO_TOKEN")
    TWILIO_FROM: str = os.getenv("TWILIO_FROM")

    PAGE_TOKEN: str = os.getenv("PAGE_TOKEN")
    APP_SECRET: str | None = os.getenv("APP_SECRET")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN")
    TEST_PSID: str | None = os.getenv("TEST_PSID")

    ENABLE_SCHEDULER: bool = False
    USE_GPT_FETCH: bool = True
    TASK_KEY: str | None = None  # used by /tasks/poll auth
    POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES"))
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY")
    DEFAULT_RADIUS_MILES: int = int(os.getenv("DEFAULT_RADIUS_MILES"))
    DEFAULT_BEDS_MIN: int = int(os.getenv("DEFAULT_BEDS_MIN"))
    DEFAULT_BATHS_MIN: int = int(os.getenv("DEFAULT_BATHS_MIN"))
    DEFAULT_MAX_PRICE: int = int(os.getenv("DEFAULT_MAX_PRICE"))


settings = Settings()
