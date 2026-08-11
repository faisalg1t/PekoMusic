"""
Peko Music — central configuration.
All values are pulled from environment variables (see .env.example).
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _list_env(key: str) -> list[int]:
    raw = os.environ.get(key, "")
    out = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            out.append(int(chunk))
    return out


class Config:
    # --- Telegram credentials ---
    API_ID = _int_env("API_ID")
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    STRING_SESSION = os.environ.get("STRING_SESSION", "")

    # --- Identity ---
    BOT_NAME = os.environ.get("BOT_NAME", "Peko Music")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "PekoMusicBot")

    # --- Database ---
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # --- Access control ---
    OWNER_ID = _int_env("OWNER_ID")
    SUDO_USERS = set(_list_env("SUDO_USERS") + ([OWNER_ID] if OWNER_ID else []))

    # --- Support links ---
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "https://t.me")
    SUPPORT_CHANNEL = os.environ.get("SUPPORT_CHANNEL", "https://t.me")

    # --- Logging ---
    LOG_GROUP_ID = _int_env("LOG_GROUP_ID")

    # --- Playback limits ---
    MAX_QUEUE_SIZE = _int_env("MAX_QUEUE_SIZE", 15)
    DURATION_LIMIT_MIN = _int_env("DURATION_LIMIT_MIN", 0)
    STREAM_QUALITY = os.environ.get("STREAM_QUALITY", "high")
    AUTO_LEAVE_MIN = _int_env("AUTO_LEAVE_MIN", 10)

    # --- yt-dlp ---
    YT_COOKIES_PATH = os.environ.get("YT_COOKIES_PATH", "") or None

    # --- Web server (keep-alive / health check) ---
    PORT = _int_env("PORT", 8080)

    START_IMG = os.environ.get(
        "START_IMG",
        "https://envs.sh/1wZ.jpg",
    )

    @classmethod
    def validate(cls):
        missing = []
        for key in ("API_ID", "API_HASH", "BOT_TOKEN", "DATABASE_URL"):
            if not getattr(cls, key):
                missing.append(key)
        if missing:
            raise SystemExit(
                f"[Peko Music] Missing required config values: {', '.join(missing)}\n"
                f"Please set them in your .env file (see .env.example)."
            )
