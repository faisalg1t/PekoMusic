from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from PekoMusic.config import Config
from PekoMusic.core.database import db
from PekoMusic.utils.inline import start_markup, help_markup, back_markup

START_TEXT = (
    "👋 Hey {mention}, I'm <b>{bot_name}</b> — a fast, feature-rich voice-chat "
    "music bot for your Telegram groups.\n\n"
    "🎧 Stream music from YouTube straight into your group's voice chat.\n"
    "⚡ High quality audio, queueing, and full playback controls.\n\n"
    "Tap <b>Commands</b> below to see what I can do, or add me to a group to get started!"
)

HELP_PLAYBACK = (
    "<b>🎵 Playback Commands</b>\n\n"
    "/play [song name or link] — play or queue a track\n"
    "/pause — pause playback\n"
    "/resume — resume playback\n"
    "/skip — skip current track\n"
    "/stop — stop and clear the queue\n"
    "/queue — view current queue\n"
    "/loop [n] — loop current track n times (0 to disable)\n"
    "/seek [seconds] — seek forward\n"
    "/mute /unmute — mute/unmute the assistant\n"
    "/current — show now-playing info"
)

HELP_ADMIN = (
    "<b>⚙️ Admin Commands</b>\n\n"
    "/auth [reply/username] — allow a user to control playback\n"
    "/unauth [reply/username] — revoke that access\n"
    "/playmode [everyone|admins] — who can control playback\n"
    "/authusers — list authorized users\n\n"
    "<b>👑 Owner/Sudo Commands</b>\n\n"
    "/broadcast [text] — message all users/chats\n"
    "/stats — bot statistics\n"
    "/addsudo /delsudo — manage sudo users\n"
    "/block /unblock — block a user bot-wide\n"
    "/logs — get the bot's log file"
)


@Client.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    if message.from_user:
        if db:
            await db.add_user(message.from_user.id)
        mention = message.from_user.mention
    else:
        mention = "there"

    if message.chat.type.name != "PRIVATE" and db:
        await db.add_chat(message.chat.id, message.chat.title or "")

    await message.reply_photo(
        photo=Config.START_IMG,
        caption=START_TEXT.format(mention=mention, bot_name=Config.BOT_NAME),
        reply_markup=start_markup(),
    )


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(
        f"<b>📚 {Config.BOT_NAME} — Command Reference</b>\n\n"
        "Select a category below.",
        reply_markup=help_markup(),
    )


@Client.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    import time

    start = time.monotonic()
    msg = await message.reply_text("🏓 Pinging...")
    latency = (time.monotonic() - start) * 1000
    await msg.edit_text(f"🏓 <b>Pong!</b> `{latency:.2f} ms`")


@Client.on_callback_query(filters.regex(r"^peko_start$"))
async def cb_start(client: Client, query: CallbackQuery):
    mention = query.from_user.mention if query.from_user else "there"
    await query.message.edit_caption(
        caption=START_TEXT.format(mention=mention, bot_name=Config.BOT_NAME),
        reply_markup=start_markup(),
    )


@Client.on_callback_query(filters.regex(r"^peko_help$"))
async def cb_help(client: Client, query: CallbackQuery):
    try:
        await query.message.edit_caption(
            caption=f"<b>📚 {Config.BOT_NAME} — Command Reference</b>\n\nSelect a category below.",
            reply_markup=help_markup(),
        )
    except Exception:
        await query.message.reply_text(
            f"<b>📚 {Config.BOT_NAME} — Command Reference</b>\n\nSelect a category below.",
            reply_markup=help_markup(),
        )


@Client.on_callback_query(filters.regex(r"^help_playback$"))
async def cb_help_playback(client: Client, query: CallbackQuery):
    try:
        await query.message.edit_caption(caption=HELP_PLAYBACK, reply_markup=back_markup("peko_help"))
    except Exception:
        await query.message.edit_text(HELP_PLAYBACK, reply_markup=back_markup("peko_help"))


@Client.on_callback_query(filters.regex(r"^help_admin$"))
async def cb_help_admin(client: Client, query: CallbackQuery):
    try:
        await query.message.edit_caption(caption=HELP_ADMIN, reply_markup=back_markup("peko_help"))
    except Exception:
        await query.message.edit_text(HELP_ADMIN, reply_markup=back_markup("peko_help"))
