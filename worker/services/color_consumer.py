import asyncio
from datetime import datetime
import os
import base64
import pickle
from typing import Any, Dict
from redis import StrictRedis as Redis
from shared_schemas import COLOR_LIST_NAME
from logger_factory import get_logger


class ColorConsumer:
    _redis: Redis | None = None
    logger = get_logger(__name__)

    def __init__(self, delay_s: float = 5, empty_print_s: int = 60):
        self._init_redis()
        self._delay_s = delay_s
        self._empty_print_s = int(empty_print_s)  # how many seconds to wait between printing empty result reminder
        self._last_pull = datetime.now()
        self._last_mod = -1

    @classmethod
    def _init_redis(cls):
        if cls._redis is None:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            cls.logger.debug(f"Connecting to Redis at {host}:{port}")
            cls._redis = Redis(host, port, decode_responses=True)

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

    async def pull_loop(self) -> None:
        if self._delay_s > 0:
            self.logger.info("Delaying for %fs before starting", self._delay_s)
            await asyncio.sleep(self._delay_s)

        if self._redis is None:
            self.logger.error("Redis connection is not initialized")
            return

        self.logger.info("Starting color consumer loop")
        while True:
            try:
                msg = self._redis.rpop(COLOR_LIST_NAME)
                if msg is None:
                    msg = self._redis.brpop([COLOR_LIST_NAME], timeout=3)
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
            except Exception as e:  # pylint: disable=broad-except
                self.logger.error("Failed to process message: %s", e)
                await asyncio.sleep(1)
                continue
