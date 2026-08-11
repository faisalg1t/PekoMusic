import asyncio
import time

import psutil
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from PekoMusic.config import Config
from PekoMusic.core.database import db
from PekoMusic.core.call import calls
from PekoMusic.utils.decorators import require_sudo, require_owner

START_TIME = time.time()


def _uptime() -> str:
    secs = int(time.time() - START_TIME)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


@Client.on_message(filters.command("stats"))
@require_sudo
async def stats_cmd(client: Client, message: Message):
    chats = len(await db.all_served_chats()) if db else 0
    users = len(await db.all_users()) if db else 0
    played = await db.get_played_count() if db else 0
    active_vc = len(calls.players)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    await message.reply_text(
        f"📊 <b>{Config.BOT_NAME} — Stats</b>\n\n"
        f"⏱ Uptime: {_uptime()}\n"
        f"💬 Served chats: {chats}\n"
        f"👤 Known users: {users}\n"
        f"🎵 Tracks played: {played}\n"
        f"🔊 Active voice chats: {active_vc}\n"
        f"🖥 CPU: {cpu}% | RAM: {ram}%"
    )


@Client.on_message(filters.command("broadcast"))
@require_sudo
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Usage: <code>/broadcast [text]</code> or reply to a message.")
        return

    text = " ".join(message.command[1:]) if len(message.command) > 1 else None
    targets = (await db.all_users() if db else []) + (await db.all_served_chats() if db else [])

    status = await message.reply_text(f"📢 Broadcasting to {len(targets)} chats...")
    sent, failed = 0, 0
    for chat_id in targets:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(chat_id)
            else:
                await client.send_message(chat_id, text)
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(f"📢 Broadcast complete.\n✅ Sent: {sent}\n❌ Failed: {failed}")


@Client.on_message(filters.command("addsudo"))
@require_owner
async def addsudo_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Reply to a user or provide a user id.")
        return
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = int(message.command[1])
    if db:
        await db.add_sudo(user_id)
    await message.reply_text(f"✅ Added <code>{user_id}</code> as a sudo user.")


@Client.on_message(filters.command("delsudo"))
@require_owner
async def delsudo_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Reply to a user or provide a user id.")
        return
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = int(message.command[1])
    if db:
        await db.remove_sudo(user_id)
    await message.reply_text(f"✅ Removed <code>{user_id}</code> from sudo users.")


@Client.on_message(filters.command("block"))
@require_sudo
async def block_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Reply to a user or provide a user id.")
        return
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    if db:
        await db.block_user(user_id)
    await message.reply_text(f"🚫 Blocked <code>{user_id}</code> from using the bot.")


@Client.on_message(filters.command("unblock"))
@require_sudo
async def unblock_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text("Reply to a user or provide a user id.")
        return
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    if db:
        await db.unblock_user(user_id)
    await message.reply_text(f"✅ Unblocked <code>{user_id}</code>.")


@Client.on_message(filters.command("logs"))
@require_sudo
async def logs_cmd(client: Client, message: Message):
    import os

    if os.path.exists("peko.log"):
        await message.reply_document("peko.log", caption="📄 Bot log file.")
    else:
        await message.reply_text("No log file found yet.")
