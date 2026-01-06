from collections.abc import AsyncGenerator
import uuid
import asyncpg
import asyncio
from pydantic import BaseModel
from datetime import datetime
from fastapi import Depends
from dotenv import load_dotenv

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FilesPath = ["users_funcs.sql","post_funcs.sql"]

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=5,
            max_size=20,
            statement_cache_size=0
        )
        async with self.pool.acquire() as conn:
         for file in FilesPath:

            with open( os.path.join(BASE_DIR, "sql",file ), "r") as f:
                await conn.execute(f.read())

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()

async def get_db():
    async with db.pool.acquire() as connection:
        yield connection