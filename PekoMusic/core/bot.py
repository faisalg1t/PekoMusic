from pyrogram import Client

from PekoMusic.config import Config


class PekoBot(Client):
    """The main bot client (controlled by users via commands)."""

    def __init__(self):
        super().__init__(
            name="PekoMusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="PekoMusic/plugins"),
            in_memory=True,
            max_concurrent_transmissions=7,
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
        return self

    async def stop(self, *args, **kwargs):
        await super().stop()


app = PekoBot()
