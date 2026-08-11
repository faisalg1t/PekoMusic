import uuid

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from PekoMusic.config import Config
from PekoMusic.core.call import calls, Track
from PekoMusic.utils import downloader
from PekoMusic.utils.decorators import require_group, require_auth
from PekoMusic.utils.inline import search_results_markup, player_markup, fmt_track_caption
from PekoMusic.logger import get_logger

log = get_logger("Peko.Play")

# Temporary in-memory store for pending multi-choice searches: query_id -> (results, message, requester)
_pending_searches: dict[str, dict] = {}


async def _build_track(result, requested_by: str, requested_by_id: int) -> Track:
    stream_url = await downloader.get_stream_url(result.webpage_url)
    return Track(
        title=result.title,
        duration=result.duration,
        duration_secs=result.duration_secs,
        stream_url=stream_url,
        thumbnail=result.thumbnail,
        requested_by=requested_by,
        requested_by_id=requested_by_id,
    )


async def _queue_and_reply(client: Client, message: Message, result, requester=None):
    chat_id = message.chat.id
    if requester:
        requested_by = requester.mention
        requested_by_id = requester.id
    else:
        requested_by = message.from_user.mention if message.from_user else "Someone"
        requested_by_id = message.from_user.id if message.from_user else 0

    if Config.DURATION_LIMIT_MIN and result.duration_secs > Config.DURATION_LIMIT_MIN * 60:
        await message.reply_text(
            f"🚫 That track is longer than the {Config.DURATION_LIMIT_MIN} minute limit set for this bot."
        )
        return

    current_queue = calls.get_queue(chat_id)
    if len(current_queue) >= Config.MAX_QUEUE_SIZE:
        await message.reply_text(
            f"🚫 Queue is full (max {Config.MAX_QUEUE_SIZE}). Wait for a track to finish or /skip."
        )
        return

    status = await message.reply_text(f"🔎 Found <b>{result.title}</b> — resolving stream...")

    try:
        track = await _build_track(result, requested_by, requested_by_id)
        position = await calls.queue_track(chat_id, track)
    except Exception as e:
        log.exception("Failed to play track")
        await status.edit_text(
            "❌ Couldn't play that track — the assistant may not be in this group's "
            "voice chat, or the voice chat isn't active.\n\n"
            f"<code>{e}</code>"
        )
        return

    has_queue = len(calls.get_queue(chat_id)) > 1
    caption = fmt_track_caption(track, position=position, queued=(position > 1))
    try:
        await status.delete()
        if track.thumbnail:
            await message.reply_photo(
                track.thumbnail,
                caption=caption,
                reply_markup=player_markup(has_queue=has_queue),
            )
        else:
            await message.reply_text(caption, reply_markup=player_markup(has_queue=has_queue))
    except Exception:
        await message.reply_text(caption, reply_markup=player_markup(has_queue=has_queue))


@Client.on_message(filters.command("play") & filters.group)
@require_group
@require_auth
async def play_cmd(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "🎵 Usage: <code>/play [song name or YouTube link]</code>\n"
            "You can also reply to an audio file."
        )
        return

    query = " ".join(message.command[1:]) if len(message.command) > 1 else None

    if not query and message.reply_to_message and message.reply_to_message.audio:
        audio = message.reply_to_message.audio
        query = audio.title or audio.file_name or ""

    if not query:
        await message.reply_text("🎵 Please provide a song name or link.")
        return

    searching = await message.reply_text(f"🔎 Searching for <b>{query}</b>...")

    try:
        # Direct link -> play top match immediately. Free text -> show picker.
        from PekoMusic.utils.downloader import YOUTUBE_RE

        if YOUTUBE_RE.search(query) or query.startswith("http"):
            result = await downloader.search(query)
            await searching.delete()
            if not result:
                await message.reply_text("❌ Couldn't find or resolve that link.")
                return
            await _queue_and_reply(client, message, result)
            return

        results = await downloader.multi_search(query, limit=8)
        await searching.delete()
        if not results:
            await message.reply_text("❌ No results found for that search.")
            return

        query_id = uuid.uuid4().hex[:10]
        _pending_searches[query_id] = {
            "results": results,
            "requester_id": message.from_user.id if message.from_user else 0,
        }
        await message.reply_text(
            f"🔎 <b>Results for:</b> {query}\n\nSelect a track to queue:",
            reply_markup=search_results_markup(results, query_id),
        )
    except Exception as e:
        log.exception("Search failed")
        try:
            await searching.edit_text(f"❌ Search failed: <code>{e}</code>")
        except Exception:
            await message.reply_text(f"❌ Search failed: <code>{e}</code>")


@Client.on_callback_query(filters.regex(r"^pick_"))
async def cb_pick_track(client: Client, query: CallbackQuery):
    _, query_id, idx = query.data.split("_", 2)
    entry = _pending_searches.get(query_id)
    if not entry:
        await query.answer("This search has expired, please search again.", show_alert=True)
        return

    if query.from_user.id != entry["requester_id"]:
        await query.answer("Only the person who searched can pick a track.", show_alert=True)
        return

    result = entry["results"][int(idx)]
    await query.answer("Queueing...")
    await query.message.delete()
    await _queue_and_reply(client, query.message, result, requester=query.from_user)
    _pending_searches.pop(query_id, None)


@Client.on_callback_query(filters.regex(r"^cancel_"))
async def cb_cancel_search(client: Client, query: CallbackQuery):
    _, query_id = query.data.split("_", 1)
    _pending_searches.pop(query_id, None)
    await query.message.delete()
    await query.answer("Cancelled.")
