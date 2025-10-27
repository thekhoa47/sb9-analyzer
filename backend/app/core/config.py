from pydantic import BaseModel
import os
from dotenv import load_dotenv


# In Cloud Run, GOOGLE_CLOUD_PROJECT is set; skip load_dotenv there.
if not os.getenv("GOOGLE_CLOUD_PROJECT"):
    load_dotenv()


class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", "8080"))
    ENV: str = os.getenv("ENV", "dev")

    BASE_URL: str = os.getenv("BASE_URL", "http://127.0.0.1:8080/api")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_URL_MIGRATIONS: str = os.getenv("DATABASE_URL_MIGRATIONS")

    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY")
    R2_BUCKET: str = os.getenv("R2_BUCKET")
    R2_S3_ENDPOINT: str = os.getenv("R2_S3_ENDPOINT")
    R2_PUBLIC_BASE: str = os.getenv("R2_PUBLIC_BASE")
    R2_ENDPOINT_URL: str = os.getenv("R2_ENDPOINT_URL") or (
        f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else None
    )

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

    EMAIL_FROM: str = os.getenv("EMAIL_FROM")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME")
    GMAIL_USER: str = os.getenv("GMAIL_USER")
    GMAIL_PASS: str = os.getenv("GMAIL_PASS")

    CRON_SECRET: str | None = os.getenv("CRON_SECRET")
    GCP_PROJECT: str = os.getenv("GCP_PROJECT", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-west1")
    CLOUD_TASKS_QUEUE_DISPATCHER: str = os.getenv(
        "CLOUD_TASKS_QUEUE_DISPATCHER", "dispatcher-jobs"
    )
    CLOUD_TASKS_QUEUE_SEARCH: str = os.getenv(
        "CLOUD_TASKS_QUEUE_SEARCH", "saved-search-jobs"
    )
    CLOUD_TASKS_QUEUE_PROPERTY: str = os.getenv(
        "CLOUD_TASKS_QUEUE_PROPERTY", "property-jobs"
    )
    CLOUD_TASKS_QUEUE_LISTING: str = os.getenv(
        "CLOUD_TASKS_QUEUE_LISTING", "listing-jobs"
    )
    TASKS_SERVICE_ACCOUNT_EMAIL: str | None = os.getenv("TASKS_SERVICE_ACCOUNT_EMAIL")
    TASKS_SHARED_SECRET: str | None = os.getenv("TASKS_SHARED_SECRET")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH")

    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME")
    SESSION_AGE: str = os.getenv("SESSION_AGE", 60 * 60 * 24 * 30)  # 7 days
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", True)


settings = Settings()
