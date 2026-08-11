# 🎶 Peko Music

A fast, production-ready Telegram voice-chat music bot built with
[Pyrogram](https://github.com/pyrogram/pyrogram),
[PyTgCalls](https://github.com/pytgcalls/pytgcalls), and
[yt-dlp](https://github.com/yt-dlp/yt-dlp).

Peko Music streams audio from YouTube (search or direct link) straight into
a group's voice chat, with full queueing, playback controls, per-group
permissions, and an admin/owner toolkit — all backed by MongoDB.

## ✨ Features

- 🔎 `/play <query>` — search YouTube or paste a link, pick from top results
- ⏯ Full playback controls — pause, resume, skip, stop, loop, seek, mute/unmute
- 📜 Per-chat queue with a configurable max size
- 🔐 `/playmode` — restrict playback control to admins, or open to everyone
- 👥 `/auth` / `/unauth` — grant specific non-admin users control
- 👑 Owner & sudo tools — `/broadcast`, `/stats`, `/addsudo`, `/block`, `/logs`
- ⏱ Auto-leave from an inactive voice chat after N minutes
- 🖥 Inline button controls attached to the "Now Playing" message
- 🩺 Built-in HTTP health-check server (for Render/Railway/Heroku-style hosts)
- 🐳 Docker + docker-compose ready, plus Heroku `Procfile`

## 🏗 Architecture

Telegram bot accounts cannot join voice chats directly — only user
accounts can. So Peko Music runs **two** Telegram clients:

1. **Bot** (`BOT_TOKEN`) — the account users talk to and send commands.
2. **Assistant** (`STRING_SESSION`) — a regular user account that joins
   the group's voice chat and streams the audio, controlled via PyTgCalls.

Both must be members of any group you want to play music in, and the
assistant account must be able to join voice chats there.

```
PekoMusic/
├── config.py          # env-driven configuration
├── logger.py
├── webserver.py        # aiohttp keep-alive server
├── generate_session.py # CLI helper to create STRING_SESSION
├── core/
│   ├── bot.py           # bot Client
│   ├── userbot.py        # assistant Client
│   ├── database.py        # MongoDB (motor) layer
│   └── call.py             # PyTgCalls wrapper: queue + playback engine
├── utils/
│   ├── downloader.py      # yt-dlp search / stream resolution
│   ├── decorators.py       # auth / permission decorators
│   └── inline.py             # keyboards & message formatting
└── plugins/
    ├── start_help.py
    ├── play.py
    ├── controls.py
    ├── admin.py
    ├── owner.py
    ├── welcome.py
    └── middleware.py
main.py                 # entrypoint
```

## 🚀 Setup

### 1. Prerequisites

- Python 3.11+
- `ffmpeg` installed and on `PATH`
- A MongoDB database (e.g. free tier on MongoDB Atlas)
- A Telegram API ID/hash from <https://my.telegram.org>
- A bot token from [@BotFather](https://t.me/BotFather)
- A second Telegram account to act as the assistant

### 2. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Make sure `ffmpeg` is installed (`apt install ffmpeg`, `brew install ffmpeg`,
or download a build for Windows).

### 3. Configure environment

```bash
cp .env.example .env
```

Fill in `API_ID`, `API_HASH`, `BOT_TOKEN`, `DATABASE_URL`, and `OWNER_ID`.

### 4. Generate the assistant's STRING_SESSION

```bash
python3 -m PekoMusic.generate_session
```

Log in with the phone number of the account that should join voice chats.
Copy the printed string into `STRING_SESSION` in your `.env`.

### 5. Run

```bash
python3 main.py
```

Add both the bot and the assistant account to your group, start a voice
chat, then run `/play <song name>` in the group.

## 🐳 Docker

```bash
docker build -t peko-music .
docker run --env-file .env -p 8080:8080 peko-music
```

Or with docker-compose (bundles a local MongoDB):

```bash
docker compose up -d
```
If using the bundled MongoDB, set `DATABASE_URL=mongodb://mongo:27017/PekoMusic`
in your `.env`.

## ☁️ Heroku-style hosting

This repo includes a `Procfile` and `runtime.txt` for platforms that use
them (Heroku, Railway with Procfile support, etc.). Deploy as a `worker`
dyno/process — it is not a web app, though it does expose a small health
endpoint on `PORT` for platforms that require one.

## ⚙️ Configuration reference

See `.env.example` for the full list of environment variables, including
queue size limits, duration limits, stream quality, and auto-leave timing.

## 🔒 Notes on the assistant account

- Use a Telegram account you're comfortable dedicating to this bot — it
  will need to join voice chats in every group you use Peko Music in.
- Respect Telegram's Terms of Service for automated/userbot accounts.
- Keep `STRING_SESSION` secret — it's equivalent to a login credential.

## 🧩 Extending

- Swap `utils/downloader.py` to add Spotify/SoundCloud resolution (the
  `spotipy` dependency is already included for metadata lookups).
- Add `/playlist` support by extending `core/database.py`'s `playlists`
  collection (scaffolded but not wired up).
- Add per-chat language support by using the `language` field already
  stored on each chat document.
