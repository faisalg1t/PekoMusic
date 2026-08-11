from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from PekoMusic.config import Config


def start_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Add me to your group", url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true"),
            ],
            [
                InlineKeyboardButton("📚 Commands", callback_data="peko_help"),
                InlineKeyboardButton("💬 Support", url=Config.SUPPORT_CHAT),
            ],
        ]
    )


def help_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎵 Playback", callback_data="help_playback"),
                InlineKeyboardButton("⚙️ Admin", callback_data="help_admin"),
            ],
            [InlineKeyboardButton("« Back", callback_data="peko_start")],
        ]
    )


def back_markup(target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data=target)]])


def player_markup(is_paused: bool = False, has_queue: bool = False) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("▶️ Resume" if is_paused else "⏸ Pause", callback_data="pcb_pauseresume"),
        InlineKeyboardButton("⏭ Skip", callback_data="pcb_skip"),
        InlineKeyboardButton("⏹ Stop", callback_data="pcb_stop"),
    ]
    row2 = [
        InlineKeyboardButton("🔇 Mute", callback_data="pcb_mute"),
        InlineKeyboardButton("🔊 Unmute", callback_data="pcb_unmute"),
    ]
    rows = [row1, row2]
    if has_queue:
        rows.append([InlineKeyboardButton("📜 Queue", callback_data="pcb_queue")])
    return InlineKeyboardMarkup(rows)


def search_results_markup(results, query_id: str) -> InlineKeyboardMarkup:
    rows = []
    for i, r in enumerate(results[:8]):
        title = r.title if len(r.title) <= 45 else r.title[:42] + "..."
        rows.append([InlineKeyboardButton(f"{i+1}. {title} [{r.duration}]", callback_data=f"pick_{query_id}_{i}")])
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data=f"cancel_{query_id}")])
    return InlineKeyboardMarkup(rows)


def fmt_track_caption(track, position: int = 1, queued: bool = False) -> str:
    if queued and position > 1:
        return (
            f"➕ <b>Added to queue at #{position}</b>\n\n"
            f"🎵 <b>{track.title}</b>\n"
            f"⏱ Duration: {track.duration}\n"
            f"🙋 Requested by: {track.requested_by}"
        )
    return (
        f"🎶 <b>Now Playing</b>\n\n"
        f"🎵 <b>{track.title}</b>\n"
        f"⏱ Duration: {track.duration}\n"
        f"🙋 Requested by: {track.requested_by}"
    )
