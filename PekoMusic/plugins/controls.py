from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from PekoMusic.core.call import calls
from PekoMusic.utils.decorators import require_group, require_auth
from PekoMusic.utils.inline import player_markup


@Client.on_message(filters.command("pause") & filters.group)
@require_group
@require_auth
async def pause_cmd(client: Client, message: Message):
    if not calls.now_playing(message.chat.id):
        await message.reply_text("❌ Nothing is playing right now.")
        return
    await calls.pause(message.chat.id)
    await message.reply_text("⏸ Paused.")


@Client.on_message(filters.command("resume") & filters.group)
@require_group
@require_auth
async def resume_cmd(client: Client, message: Message):
    if not calls.now_playing(message.chat.id):
        await message.reply_text("❌ Nothing is playing right now.")
        return
    await calls.resume(message.chat.id)
    await message.reply_text("▶️ Resumed.")


@Client.on_message(filters.command("skip") & filters.group)
@require_group
@require_auth
async def skip_cmd(client: Client, message: Message):
    if not calls.now_playing(message.chat.id):
        await message.reply_text("❌ Nothing is playing right now.")
        return
    nxt = await calls.skip(message.chat.id)
    if nxt:
        await message.reply_text(f"⏭ Skipped. Now playing: <b>{nxt.title}</b>")
    else:
        await message.reply_text("⏭ Skipped. Queue is now empty — left the voice chat.")


@Client.on_message(filters.command("stop") & filters.group)
@require_group
@require_auth
async def stop_cmd(client: Client, message: Message):
    await calls.stop(message.chat.id)
    await message.reply_text("⏹ Stopped playback and cleared the queue.")


@Client.on_message(filters.command(["mute"]) & filters.group)
@require_group
@require_auth
async def mute_cmd(client: Client, message: Message):
    await calls.mute(message.chat.id)
    await message.reply_text("🔇 Muted.")


@Client.on_message(filters.command(["unmute"]) & filters.group)
@require_group
@require_auth
async def unmute_cmd(client: Client, message: Message):
    await calls.unmute(message.chat.id)
    await message.reply_text("🔊 Unmuted.")


@Client.on_message(filters.command("current") & filters.group)
@require_group
async def current_cmd(client: Client, message: Message):
    track = calls.now_playing(message.chat.id)
    if not track:
        await message.reply_text("❌ Nothing is playing right now.")
        return
    await message.reply_text(
        f"🎶 <b>Now Playing</b>\n\n"
        f"🎵 {track.title}\n"
        f"⏱ Duration: {track.duration}\n"
        f"🙋 Requested by: {track.requested_by}"
    )


@Client.on_message(filters.command("queue") & filters.group)
@require_group
async def queue_cmd(client: Client, message: Message):
    q = calls.get_queue(message.chat.id)
    if not q:
        await message.reply_text("📭 The queue is empty.")
        return
    lines = [f"📜 <b>Queue for {message.chat.title}</b>\n"]
    for i, t in enumerate(q[:20]):
        marker = "▶️" if i == 0 else f"{i}."
        lines.append(f"{marker} {t.title} — {t.duration} (by {t.requested_by})")
    if len(q) > 20:
        lines.append(f"\n...and {len(q) - 20} more.")
    await message.reply_text("\n".join(lines))


@Client.on_message(filters.command("loop") & filters.group)
@require_group
@require_auth
async def loop_cmd(client: Client, message: Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        await message.reply_text("Usage: <code>/loop [number]</code> — e.g. <code>/loop 3</code>, or <code>/loop 0</code> to disable.")
        return
    n = int(message.command[1])
    calls.set_loop(message.chat.id, n)
    if n == 0:
        await message.reply_text("🔁 Loop disabled.")
    else:
        await message.reply_text(f"🔁 Current track will repeat {n} more time(s).")


@Client.on_message(filters.command("seek") & filters.group)
@require_group
@require_auth
async def seek_cmd(client: Client, message: Message):
    track = calls.now_playing(message.chat.id)
    if not track:
        await message.reply_text("❌ Nothing is playing right now.")
        return
    if len(message.command) < 2 or not message.command[1].isdigit():
        await message.reply_text("Usage: <code>/seek [seconds]</code>")
        return
    seconds = int(message.command[1])
    await calls.seek(message.chat.id, track, seconds)
    await message.reply_text(f"⏩ Seeked to {seconds}s (restarts stream at that offset where supported).")


# ------------------------------------------------------------- callback UI
@Client.on_callback_query(filters.regex(r"^pcb_"))
async def playback_callbacks(client: Client, query: CallbackQuery):
    action = query.data.split("_", 1)[1]
    chat_id = query.message.chat.id

    if action == "pauseresume":
        track = calls.now_playing(chat_id)
        if not track:
            await query.answer("Nothing is playing.", show_alert=True)
            return
        player = calls._player(chat_id)
        if player.is_paused:
            await calls.resume(chat_id)
            await query.answer("Resumed ▶️")
        else:
            await calls.pause(chat_id)
            await query.answer("Paused ⏸")
        try:
            await query.message.edit_reply_markup(
                player_markup(is_paused=not player.is_paused, has_queue=len(calls.get_queue(chat_id)) > 1)
            )
        except Exception:
            pass

    elif action == "skip":
        nxt = await calls.skip(chat_id)
        await query.answer("Skipped ⏭")
        if nxt:
            await query.message.reply_text(f"⏭ Now playing: <b>{nxt.title}</b>")

    elif action == "stop":
        await calls.stop(chat_id)
        await query.answer("Stopped ⏹")
        await query.message.reply_text("⏹ Stopped playback and cleared the queue.")

    elif action == "mute":
        await calls.mute(chat_id)
        await query.answer("Muted 🔇")

    elif action == "unmute":
        await calls.unmute(chat_id)
        await query.answer("Unmuted 🔊")

    elif action == "queue":
        q = calls.get_queue(chat_id)
        if not q:
            await query.answer("Queue is empty.", show_alert=True)
            return
        lines = [f"{i+1}. {t.title} — {t.duration}" for i, t in enumerate(q[:10])]
        await query.answer("\n".join(lines)[:200], show_alert=True)
