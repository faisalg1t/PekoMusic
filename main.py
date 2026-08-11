import asyncio
import sys

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

from PekoMusic.config import Config
from PekoMusic.logger import get_logger
from PekoMusic.core.bot import app
from PekoMusic.core.userbot import assistant
from PekoMusic.core.call import calls
from PekoMusic.webserver import run_web_server

log = get_logger("Peko.Main")


async def main():
    Config.validate()

    log.info("Starting %s ...", Config.BOT_NAME)

    await app.start()
    log.info("Bot client started as @%s", app.username)

    await assistant.start()

    await calls.start()

    await run_web_server()
    log.info("Keep-alive web server running on port %s", Config.PORT)

    if Config.LOG_GROUP_ID:
        try:
            await app.send_message(
                Config.LOG_GROUP_ID,
                f"✅ <b>{Config.BOT_NAME}</b> started successfully.\n"
                f"Bot: @{app.username}\nAssistant: {assistant.name}",
            )
        except Exception as e:
            log.warning("Could not send startup message to LOG_GROUP_ID: %s", e)

    log.info("%s is now up and running. Press CTRL+C to stop.", Config.BOT_NAME)

    await idle()

    log.info("Shutting down...")
    await app.stop()
    await assistant.stop()


async def idle():
    """Block forever until interrupted (SIGINT/SIGTERM)."""
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig_name in ("SIGINT", "SIGTERM"):
        try:
            import signal

            loop.add_signal_handler(getattr(signal, sig_name), stop_event.set)
        except (NotImplementedError, AttributeError):
            pass  # Windows fallback

    await stop_event.wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Interrupted, exiting.")
        sys.exit(0)
