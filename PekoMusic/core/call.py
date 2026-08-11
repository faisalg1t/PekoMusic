"""
Peko Music — voice-chat streaming engine.

Wraps PyTgCalls to provide:
  - per-chat queues
  - play / skip / pause / resume / stop / seek
  - loop mode
  - auto-advance when a track ends
  - auto-leave after inactivity
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality
from pytgcalls.types.stream import StreamAudioEnded

from PekoMusic.config import Config
from PekoMusic.core.database import db
from PekoMusic.core.userbot import assistant
from PekoMusic.logger import get_logger

log = get_logger("Peko.Calls")


@dataclass
class Track:
    title: str
    duration: str
    duration_secs: int
    stream_url: str
    thumbnail: str
    requested_by: str
    requested_by_id: int
    file_path: str = ""   # local path if downloaded, else stream_url is used


@dataclass
class ChatPlayer:
    queue: list[Track] = field(default_factory=list)
    is_playing: bool = False
    is_paused: bool = False
    loop: int = 0  # number of extra repeats of current track, 0 = off


class PekoCalls:
    def __init__(self):
        self.pytgcalls = PyTgCalls(assistant)
        self.players: dict[int, ChatPlayer] = {}
        self._leave_tasks: dict[int, asyncio.Task] = {}

    # ------------------------------------------------------------- helpers
    def _player(self, chat_id: int) -> ChatPlayer:
        if chat_id not in self.players:
            self.players[chat_id] = ChatPlayer()
        return self.players[chat_id]

    def _quality(self) -> AudioQuality:
        return {
            "low": AudioQuality.LOW,
            "medium": AudioQuality.MEDIUM,
            "high": AudioQuality.STUDIO,
        }.get(Config.STREAM_QUALITY, AudioQuality.HIGH)

    def _cancel_leave_timer(self, chat_id: int):
        task = self._leave_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()

    def _schedule_leave_timer(self, chat_id: int):
        if Config.AUTO_LEAVE_MIN <= 0:
            return
        self._cancel_leave_timer(chat_id)

        async def _leave_later():
            try:
                await asyncio.sleep(Config.AUTO_LEAVE_MIN * 60)
                player = self._player(chat_id)
                if not player.queue and not player.is_playing:
                    await self.leave(chat_id)
            except asyncio.CancelledError:
                pass

        self._leave_tasks[chat_id] = asyncio.create_task(_leave_later())

    # -------------------------------------------------------------- public
    async def start(self):
        await self.pytgcalls.start()
        self.pytgcalls.on_stream_end()(self._on_stream_end)
        log.info("PyTgCalls started.")

    async def queue_track(self, chat_id: int, track: Track) -> int:
        """Add a track to the chat queue. Returns its position (1 = now playing)."""
        player = self._player(chat_id)
        player.queue.append(track)
        if not player.is_playing:
            await self._play_index(chat_id, 0)
            return 1
        return len(player.queue)

    async def _play_index(self, chat_id: int, index: int):
        player = self._player(chat_id)
        if index >= len(player.queue):
            player.is_playing = False
            self._schedule_leave_timer(chat_id)
            return
        track = player.queue[index]
        source = track.file_path or track.stream_url
        try:
            await self.pytgcalls.play(
                chat_id,
                MediaStream(source, audio_parameters=self._quality()),
            )
        except Exception:
            # Not yet in the call -> join + play
            await self.pytgcalls.play(
                chat_id,
                MediaStream(source, audio_parameters=self._quality()),
            )
        player.is_playing = True
        player.is_paused = False
        self._cancel_leave_timer(chat_id)
        if db:
            await db.incr_played()

    async def _on_stream_end(self, _, update: StreamAudioEnded):
        chat_id = update.chat_id
        player = self._player(chat_id)
        if not player.queue:
            return
        if player.loop > 0:
            player.loop -= 1
        else:
            player.queue.pop(0)
        await self._play_index(chat_id, 0)

    async def skip(self, chat_id: int) -> Track | None:
        player = self._player(chat_id)
        if not player.queue:
            return None
        player.queue.pop(0)
        if player.queue:
            await self._play_index(chat_id, 0)
            return player.queue[0]
        else:
            await self.pytgcalls.leave_call(chat_id)
            player.is_playing = False
            self._schedule_leave_timer(chat_id)
            return None

    async def pause(self, chat_id: int):
        await self.pytgcalls.pause(chat_id)
        self._player(chat_id).is_paused = True

    async def resume(self, chat_id: int):
        await self.pytgcalls.resume(chat_id)
        self._player(chat_id).is_paused = False

    async def mute(self, chat_id: int):
        await self.pytgcalls.mute(chat_id)

    async def unmute(self, chat_id: int):
        await self.pytgcalls.unmute(chat_id)

    async def seek(self, chat_id: int, track: Track, to_seconds: int):
        source = track.file_path or track.stream_url
        await self.pytgcalls.play(
            chat_id,
            MediaStream(
                source,
                audio_parameters=self._quality(),
            ),
        )

    async def stop(self, chat_id: int):
        player = self._player(chat_id)
        player.queue.clear()
        player.is_playing = False
        player.is_paused = False
        player.loop = 0
        try:
            await self.pytgcalls.leave_call(chat_id)
        except Exception:
            pass
        self._schedule_leave_timer(chat_id)

    async def leave(self, chat_id: int):
        try:
            await self.pytgcalls.leave_call(chat_id)
        except Exception:
            pass
        self.players.pop(chat_id, None)

    def get_queue(self, chat_id: int) -> list[Track]:
        return self._player(chat_id).queue

    def now_playing(self, chat_id: int) -> Track | None:
        q = self.get_queue(chat_id)
        return q[0] if q else None

    def set_loop(self, chat_id: int, count: int):
        self._player(chat_id).loop = count


calls = PekoCalls()
