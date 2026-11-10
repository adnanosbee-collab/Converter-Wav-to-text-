import os
from dotenv import load_dotenv

load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")
MAX_DURATION_SECONDS = int(os.getenv("MAX_DURATION_SECONDS", "10800"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(1024**3)))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/uploads")

AUTH_SECRET = os.getenv("AUTH_SECRET")
if not AUTH_SECRET:
    raise RuntimeError("AUTH_SECRET environment variable is not configured.")

AUTH_TOKEN_EXPIRE_HOURS = int(os.getenv("AUTH_TOKEN_EXPIRE_HOURS", "12"))
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
