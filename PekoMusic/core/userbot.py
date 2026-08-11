from pyrogram import Client

from PekoMusic.config import Config
from PekoMusic.logger import get_logger

log = get_logger("Peko.Assistant")


class PekoAssistant(Client):
    """
    The assistant account that physically joins voice chats and streams
    audio. Telegram bot accounts cannot join VCs themselves, so a regular
    user account (via STRING_SESSION) is required for this — this is how
    every VC-streaming Telegram music bot works.
    """

    def __init__(self):
        if not Config.STRING_SESSION:
            raise SystemExit(
                "[Peko Music] STRING_SESSION is not set. Generate one with:\n"
                "  python3 -m PekoMusic.generate_session"
            )
        super().__init__(
            name="PekoAssistant",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.STRING_SESSION,
            in_memory=True,
        )
        self.id = None
        self.username = None
        self.name = None
        self.mention = None

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.id = me.id
        self.username = me.username
        self.name = me.first_name
        self.mention = me.mention
        log.info("Assistant started as %s", self.name)
        return self

    async def stop(self, *args, **kwargs):
        await super().stop()


assistant = PekoAssistant()
