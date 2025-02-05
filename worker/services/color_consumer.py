import asyncio
import base64
import os
import pickle
from datetime import datetime
import random
from typing import Any, Dict
import json
import asyncpg
from fastapi.encoders import jsonable_encoder
from logger_factory import get_logger
from redis import StrictRedis as Redis
from shared_schemas import COLOR_LIST_NAME


class ColorConsumer:
    _redis: Redis | None = None
    _pg_conn: asyncpg.Connection | None = None
    logger = get_logger(__name__)

    def __init__(self, empty_delay_s: float = 3, empty_print_s: int = 60):
        self._init_redis()
        self._empty_delay_s = empty_delay_s
        self._empty_print_s = int(empty_print_s)  # how many seconds to wait between printing empty result reminder
        self._last_pull = datetime.now()
        self._last_mod = -1

        self.min_delay = int(os.getenv("WORKER_DELAY_MIN", "0"))
        self.max_delay = int(os.getenv("WORKER_DELAY_MAX", "0"))
        self.can_delay = self.min_delay < self.max_delay and self.max_delay > 0
        self.is_random_delay = self.can_delay and self.min_delay < self.max_delay

    @classmethod
    def _init_redis(cls):
        if cls._redis is None:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            cls.logger.debug("Connecting to Redis at %s:%d", host, port)
            cls._redis = Redis(host, port, decode_responses=True)

    @classmethod
    async def _init_pg(cls):
        if cls._pg_conn is None:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = int(os.getenv("POSTGRES_PORT", "5432"))
            schema = os.getenv("POSTGRES_DB", "dev")
            user = os.getenv("POSTGRES_USER", "pguser")
            pwd = os.getenv("POSTGRES_PASSWORD", "pgpass")
            cls.logger.debug("Connecting to PostgreSQL db: %s at: %s:%d", schema, host, port)
            cls._pg_conn = await asyncpg.connect(
                user=user, password=pwd, database=schema, host=host, port=port)

    @classmethod
    async def cleanup(cls) -> None:
        if cls._pg_conn is not None:
            await cls._pg_conn.close()
            cls._pg_conn = None

    def _unwrap(self, msg: Any) -> Dict[str, Any]:
        if msg is None:
            self.logger.error("Received message is None")
            return {}
        s: str = ""
        if isinstance(msg, str):
            s = msg
        if isinstance(msg, tuple) and len(msg) == 2 and isinstance(msg[1], str):
            s = str(msg[1])
        if not s:
            self.logger.error("Received message is not a string: %s", msg)
            return {}

        buf = base64.b64decode(s, validate=True)
        data: Dict[str, Any] = pickle.loads(buf)
        return data

    async def pull_event_loop(self) -> None:
        if self._empty_delay_s > 0:
            self.logger.info("Delaying for %fs before starting", self._empty_delay_s)
            await asyncio.sleep(self._empty_delay_s)

        if self._redis is None:
            self.logger.error("Redis connection is not initialized")
            return

        self.logger.info("Starting color consumer loop")
        while True:
            try:
                msg = self._redis.rpop(COLOR_LIST_NAME)
                if msg is None:
                    msg = self._redis.brpop([COLOR_LIST_NAME], timeout=int(self._empty_delay_s))
                if not msg:
                    since_sec = int((datetime.now() - self._last_pull).total_seconds())
                    mod_count = since_sec % self._empty_print_s
                    block = since_sec - mod_count
                    if self._last_mod != block:
                        self._last_mod = block
                        self.logger.debug("No messages in the last %d seconds. Since: %s", since_sec, self._last_pull)
                    continue  # repeat loop, still empty
                else:
                    self._last_pull = datetime.now()

                data: Dict[str, Any] = self._unwrap(msg)
                self.logger.debug("Received color match event: %s", data)

                await self._write_to_db(data)
                if self.can_delay:
                    delay_ms = self.min_delay
                    if self.is_random_delay:
                        delay_ms = random.randint(self.min_delay, self.max_delay)
                    self.logger.debug("Delaying for %dms before next message", delay_ms)
                    await asyncio.sleep(delay_ms / 1000)

            except Exception as e:  # pylint: disable=broad-except
                self.logger.error("Failed to process message: %s", e)
                await asyncio.sleep(1)
                continue

    async def _write_to_db(self, data: Dict[str, Any]) -> None:
        if self._pg_conn is None:
            await self._init_pg()
        if self._pg_conn is None:
            self.logger.error("PostgreSQL connection is not initialized")
            return

        usr = data.get("user", None)
        if usr is None:
            self.logger.warning("User not found in message: %s", data)
            return
        run = data.get("run", None)
        if run is None:
            self.logger.warning("Run not found in message: %s", data)
            return
        name = data.get("input", None)
        if name is None:
            self.logger.warning("Input not found in message: %s", data)
            return

        del data["user"]
        del data["run"]
        del data["input"]
        obj = jsonable_encoder(data)
        js = json.dumps(obj)

        ok = await self._pg_conn.execute(
            "INSERT INTO color_matches (usr, run, input, body) VALUES ($1, $2, $3, $4);",
            usr, run, name, js)
        self.logger.debug(
            "%s color match result for usr: %s, run: %s, input: %s",
            ok, usr, run, name)
