from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatType

from PekoMusic.core.database import db


async def _requires_group_admin(client: Client, message: Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text("This command only works in groups.")
        return False
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
        await message.reply_text("🚫 Only group admins can use this command.")
        return False
    return True


async def _resolve_target_user(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        target = message.command[1]
        try:
            return await client.get_users(target)
        except Exception:
            return None
    return None


@Client.on_message(filters.command("auth") & filters.group)
async def auth_cmd(client: Client, message: Message):
    if not await _requires_group_admin(client, message):
        return
    user = await _resolve_target_user(client, message)
    if not user:
        await message.reply_text("Reply to a user or provide a username to authorize.\nUsage: <code>/auth @username</code>")
        return
    if db:
        await db.add_auth_user(message.chat.id, user.id)
    await message.reply_text(f"✅ {user.mention} can now control playback in this group.")


@Client.on_message(filters.command("unauth") & filters.group)
async def unauth_cmd(client: Client, message: Message):
    if not await _requires_group_admin(client, message):
        return
    user = await _resolve_target_user(client, message)
    if not user:
        await message.reply_text("Reply to a user or provide a username to revoke.\nUsage: <code>/unauth @username</code>")
        return
    if db:
        await db.remove_auth_user(message.chat.id, user.id)
    await message.reply_text(f"✅ {user.mention}'s playback access has been revoked.")


@Client.on_message(filters.command("authusers") & filters.group)
async def authusers_cmd(client: Client, message: Message):
    if not db:
        await message.reply_text("Database not configured.")
        return
    users = await db.get_auth_users(message.chat.id)
    if not users:
        await message.reply_text("No additional authorized users in this group.")
        return
    lines = ["👥 <b>Authorized users:</b>"]
    for uid in users:
        try:
            u = await client.get_users(uid)
            lines.append(f"• {u.mention}")
        except Exception:
            lines.append(f"• <code>{uid}</code>")
    await message.reply_text("\n".join(lines))


@Client.on_message(filters.command("playmode") & filters.group)
async def playmode_cmd(client: Client, message: Message):
    if not await _requires_group_admin(client, message):
        return
    if len(message.command) < 2 or message.command[1].lower() not in ("everyone", "admins"):
        current = await db.get_playmode(message.chat.id) if db else "everyone"
        await message.reply_text(
            f"Current mode: <b>{current}</b>\n"
            "Usage: <code>/playmode everyone</code> or <code>/playmode admins</code>"
        )
        return
    mode = message.command[1].lower()
    if db:
        await db.set_playmode(message.chat.id, mode)
    await message.reply_text(f"✅ Playback control mode set to <b>{mode}</b>.")
