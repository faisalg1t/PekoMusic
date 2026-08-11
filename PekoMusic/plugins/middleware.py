from pyrogram import Client, filters
from pyrogram.types import Message

from PekoMusic.core.database import db


@Client.on_message(filters.group & ~filters.service, group=-1)
async def _track_chat(client: Client, message: Message):
    if db and message.chat:
        await db.add_chat(message.chat.id, message.chat.title or "")
    if db and message.from_user:
        await db.add_user(message.from_user.id)


@Client.on_message(filters.private & filters.incoming, group=-1)
async def _track_user(client: Client, message: Message):
    if db and message.from_user:
        await db.add_user(message.from_user.id)


@Client.on_message(filters.incoming & filters.command(
    ["play", "pause", "resume", "skip", "stop", "queue", "current",
     "loop", "seek", "mute", "unmute", "auth", "unauth", "playmode"]
), group=-2)
async def _block_gate(client: Client, message: Message):
    if db and message.from_user and await db.is_blocked(message.from_user.id):
        await message.reply_text("🚫 You have been blocked from using this bot.")
        message.stop_propagation()
