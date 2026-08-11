from functools import wraps

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from PekoMusic.config import Config
from PekoMusic.core.database import db


async def is_admin_or_auth(client: Client, message: Message) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    if user_id in Config.SUDO_USERS:
        return True
    if db and user_id in await db.get_sudoers():
        return True
    if message.chat.type.name == "PRIVATE":
        return True
    member = await client.get_chat_member(message.chat.id, user_id)
    if member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
        return True
    if db and user_id in await db.get_auth_users(message.chat.id):
        return True
    return False


def require_group(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        if message.chat.type.name == "PRIVATE":
            await message.reply_text(
                "🚫 This command only works in groups with an active voice chat."
            )
            return
        return await func(client, message, *args, **kwargs)

    return wrapper


def require_auth(func):
    """Restrict playback-control commands to admins / auth users (per chat setting)."""

    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        if message.chat.type.name != "PRIVATE" and db:
            mode = await db.get_playmode(message.chat.id)
            if mode == "admins" and not await is_admin_or_auth(client, message):
                await message.reply_text(
                    "🚫 Only group admins or authorized users can control playback here.\n"
                    "Ask an admin to use /auth to give you access."
                )
                return
        return await func(client, message, *args, **kwargs)

    return wrapper


def require_sudo(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else 0
        sudoers = Config.SUDO_USERS
        if db:
            sudoers = sudoers | set(await db.get_sudoers())
        if user_id not in sudoers:
            await message.reply_text("🚫 This command is restricted to bot sudo users.")
            return
        return await func(client, message, *args, **kwargs)

    return wrapper


def require_owner(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else 0
        if user_id != Config.OWNER_ID:
            await message.reply_text("🚫 This command is restricted to the bot owner.")
            return
        return await func(client, message, *args, **kwargs)

    return wrapper
