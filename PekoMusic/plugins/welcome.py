from pyrogram import Client, filters
from pyrogram.types import Message

from PekoMusic.config import Config
from PekoMusic.core.database import db


@Client.on_message(filters.new_chat_members)
async def on_added_to_group(client: Client, message: Message):
    added_ids = [u.id for u in message.new_chat_members]
    if client.me and client.me.id in added_ids:
        if db:
            await db.add_chat(message.chat.id, message.chat.title or "")
        await message.reply_text(
            f"👋 Thanks for adding me to <b>{message.chat.title}</b>!\n\n"
            "Start a voice chat and use /play [song name] to begin streaming music.\n"
            "Use /help to see all commands."
        )
        if Config.LOG_GROUP_ID:
            try:
                await client.send_message(
                    Config.LOG_GROUP_ID,
                    f"➕ Added to a new chat: <b>{message.chat.title}</b> (<code>{message.chat.id}</code>)",
                )
            except Exception:
                pass


@Client.on_message(filters.left_chat_member)
async def on_removed_from_group(client: Client, message: Message):
    if message.left_chat_member and client.me and message.left_chat_member.id == client.me.id:
        if db:
            await db.remove_chat(message.chat.id)
