"""
Peko Music — search & extraction layer built on yt-dlp.

Supports:
  - Free-text search (YouTube)
  - Direct YouTube / Spotify(track name fallback) links
  - Metadata-only extraction for fast queueing (stream URL resolved lazily)
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass

import yt_dlp

from PekoMusic.config import Config
from PekoMusic.logger import get_logger

log = get_logger("Peko.Downloader")

COOKIE_OPTS = {"cookiefile": Config.YT_COOKIES_PATH} if Config.YT_COOKIES_PATH else {}

YOUTUBE_RE = re.compile(
    r"(?:youtube\.com|youtu\.be)", re.IGNORECASE
)


@dataclass
class SearchResult:
    title: str
    duration: str
    duration_secs: int
    webpage_url: str
    thumbnail: str
    uploader: str


def _fmt_duration(secs: int) -> str:
    if not secs:
        return "Live"
    secs = int(secs)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _base_opts() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "extract_flat": False,
        **COOKIE_OPTS,
    }


async def _run(fn, *args, **kwargs):
    """Run a blocking yt-dlp call in a thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


def _search_sync(query: str) -> SearchResult | None:
    opts = _base_opts()
    with yt_dlp.YoutubeDL(opts) as ydl:
        if YOUTUBE_RE.search(query):
            info = ydl.extract_info(query, download=False)
        else:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if "entries" in info:
                if not info["entries"]:
                    return None
                info = info["entries"][0]
        return SearchResult(
            title=info.get("title", "Unknown"),
            duration=_fmt_duration(info.get("duration", 0)),
            duration_secs=int(info.get("duration") or 0),
            webpage_url=info.get("webpage_url", query),
            thumbnail=(info.get("thumbnail") or ""),
            uploader=info.get("uploader", "Unknown"),
        )


def _multi_search_sync(query: str, limit: int = 8) -> list[SearchResult]:
    opts = _base_opts()
    opts["extract_flat"] = "in_playlist"
    results = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        for entry in info.get("entries", []) or []:
            if not entry:
                continue
            results.append(
                SearchResult(
                    title=entry.get("title", "Unknown"),
                    duration=_fmt_duration(entry.get("duration", 0)),
                    duration_secs=int(entry.get("duration") or 0),
                    webpage_url=entry.get("url")
                    or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    thumbnail=(entry.get("thumbnail") or ""),
                    uploader=entry.get("uploader", "Unknown"),
                )
            )
    return results


def _stream_url_sync(webpage_url: str) -> str:
    opts = _base_opts()
    opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(webpage_url, download=False)
        return info["url"]


def _download_sync(webpage_url: str, out_dir: str = "downloads") -> str:
    os.makedirs(out_dir, exist_ok=True)
    opts = _base_opts()
    opts.update(
        {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "opus",
                    "preferredquality": "192",
                }
            ],
        }
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(webpage_url, download=True)
        base = os.path.join(out_dir, info["id"])
        for ext in ("opus", "m4a", "webm", "mp3"):
            path = f"{base}.{ext}"
            if os.path.exists(path):
                return path
        return ydl.prepare_filename(info)


# ------------------------------------------------------------------ public
async def search(query: str) -> SearchResult | None:
    return await _run(_search_sync, query)


async def multi_search(query: str, limit: int = 8) -> list[SearchResult]:
    return await _run(_multi_search_sync, query, limit)


async def get_stream_url(webpage_url: str) -> str:
    return await _run(_stream_url_sync, webpage_url)


async def download(webpage_url: str) -> str:
    return await _run(_download_sync, webpage_url)
