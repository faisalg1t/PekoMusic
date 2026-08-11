"""
Peko Music — MongoDB persistence layer (async, via motor).

Collections:
  chats        -> per-chat settings (language, auth users, playmode)
  users        -> known users (for /broadcast and stats)
  sudoers      -> extra bot-wide admins
  blocked      -> globally blocked users
  gban         -> globally banned users (per-chat enforcement)
  playlists    -> saved playlists per user (optional feature)
  stats        -> global counters (songs played, etc.)
"""

from __future__ import annotations

import motor.motor_asyncio

from PekoMusic.config import Config
from PekoMusic.logger import get_logger

log = get_logger("Peko.Database")


class Database:
    def __init__(self, uri: str):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client["PekoMusic"]

        self.chats = self.db.chats
        self.users = self.db.users
        self.sudoers = self.db.sudoers
        self.blocked = self.db.blocked_users
        self.authusers = self.db.auth_users
        self.stats = self.db.stats

    # ---------------------------------------------------------------- users
    async def add_user(self, user_id: int):
        if not await self.users.find_one({"user_id": user_id}):
            await self.users.insert_one({"user_id": user_id})

    async def all_users(self) -> list[int]:
        return [doc["user_id"] async for doc in self.users.find({})]

    async def is_blocked(self, user_id: int) -> bool:
        return bool(await self.blocked.find_one({"user_id": user_id}))

    async def block_user(self, user_id: int):
        if not await self.is_blocked(user_id):
            await self.blocked.insert_one({"user_id": user_id})

    async def unblock_user(self, user_id: int):
        await self.blocked.delete_one({"user_id": user_id})

    # ---------------------------------------------------------------- chats
    async def add_chat(self, chat_id: int, title: str = ""):
        if not await self.chats.find_one({"chat_id": chat_id}):
            await self.chats.insert_one(
                {
                    "chat_id": chat_id,
                    "title": title,
                    "language": "en",
                    "playmode": "everyone",  # everyone | admins
                    "auth_users": [],
                }
            )

    async def remove_chat(self, chat_id: int):
        await self.chats.delete_one({"chat_id": chat_id})

    async def all_served_chats(self) -> list[int]:
        return [doc["chat_id"] async for doc in self.chats.find({})]

    async def get_playmode(self, chat_id: int) -> str:
        doc = await self.chats.find_one({"chat_id": chat_id})
        return doc.get("playmode", "everyone") if doc else "everyone"

    async def set_playmode(self, chat_id: int, mode: str):
        await self.chats.update_one(
            {"chat_id": chat_id}, {"$set": {"playmode": mode}}, upsert=True
        )

    async def get_auth_users(self, chat_id: int) -> list[int]:
        doc = await self.chats.find_one({"chat_id": chat_id})
        return doc.get("auth_users", []) if doc else []

    async def add_auth_user(self, chat_id: int, user_id: int):
        await self.chats.update_one(
            {"chat_id": chat_id}, {"$addToSet": {"auth_users": user_id}}, upsert=True
        )

    async def remove_auth_user(self, chat_id: int, user_id: int):
        await self.chats.update_one(
            {"chat_id": chat_id}, {"$pull": {"auth_users": user_id}}
        )

    # -------------------------------------------------------------- sudoers
    async def get_sudoers(self) -> list[int]:
        return [doc["user_id"] async for doc in self.sudoers.find({})]

    async def add_sudo(self, user_id: int):
        if not await self.sudoers.find_one({"user_id": user_id}):
            await self.sudoers.insert_one({"user_id": user_id})

    async def remove_sudo(self, user_id: int):
        await self.sudoers.delete_one({"user_id": user_id})

    # --------------------------------------------------------------- stats
    async def incr_played(self, n: int = 1):
        await self.stats.update_one(
            {"_id": "global"}, {"$inc": {"songs_played": n}}, upsert=True
        )

    async def get_played_count(self) -> int:
        doc = await self.stats.find_one({"_id": "global"})
        return doc.get("songs_played", 0) if doc else 0


db = Database(Config.DATABASE_URL) if Config.DATABASE_URL else None
