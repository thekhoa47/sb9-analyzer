# app/core/model.py
import logging
import boto3
from botocore.client import Config
from pathlib import Path
from app.core.config import settings
from app.ml.sb9_model import SB9Runner

log = logging.getLogger("sb9")


class ModelManager:
    def __init__(self):
        self.model_runner: SB9Runner | None = None

    def _get_r2_client(self):
        if not (
            settings.R2_ACCESS_KEY_ID
            and settings.R2_SECRET_ACCESS_KEY
            and settings.R2_ENDPOINT_URL
        ):
            raise RuntimeError(
                "R2 credentials/endpoint not configured for model download"
            )
        session = boto3.session.Session()
        return session.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def _ensure_local_model(self) -> Path:
        """
        Ensure the model file exists under MODEL_CACHE_DIR/R2_MODEL_KEY.
        If missing, download once from R2. Returns local path.
        """
        local_path = settings.MODEL_CACHE_DIR / settings.R2_MODEL_KEY
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if not local_path.exists() or local_path.stat().st_size == 0:
            s3 = self._get_r2_client()
            # stream to temp then rename (atomic-ish)
            tmp_path = local_path.with_suffix(local_path.suffix + ".part")
            with (
                s3.get_object(
                    Bucket=settings.R2_MODEL_BUCKET, Key=settings.R2_MODEL_KEY
                )["Body"] as body,
                open(tmp_path, "wb") as f,
            ):
                for chunk in iter(lambda: body.read(1024 * 1024), b""):
                    f.write(chunk)
            tmp_path.replace(local_path)
            print(
                f"[SB9] Downloaded model from r2://{settings.R2_MODEL_BUCKET}/{settings.R2_MODEL_KEY} -> {local_path}"
            )
        else:
            print(f"[SB9] Using cached model at {local_path}")
        return local_path

    async def load_model(self):
        """Load the model into memory"""
        try:
            model_path = self._ensure_local_model()
            self.model_runner = SB9Runner(str(model_path))
            log.info("[SB9] Model loaded ✅")
        except Exception as e:
            self.model_runner = None
            log.exception("[SB9] Model load error: %s: %s", type(e).__name__, e)
            raise

    def unload_model(self):
        """Unload the model from memory"""
        self.model_runner = None
        log.info("[SB9] Model unloaded")

    @property
    def is_loaded(self) -> bool:
        return self.model_runner is not None


model_manager = ModelManager()
