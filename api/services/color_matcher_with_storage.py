from typing import Any, List
import os
import base64
import binascii
import pickle
from datetime import datetime
from fastapi import Request
from redis import Redis
from services.color_matcher import ColorMatcherABC
from services.schemas import ColorMatched
from logger import get_logger


class ColorMatcherWithStorage(ColorMatcherABC):
    _redis: Redis | None = None
    logger = get_logger(__name__)

    def __init__(self, matcher: ColorMatcherABC, request: Request):
        self.__matcher = matcher
        self.request = request
        self._init_redis()

    @classmethod
    def _init_redis(cls):
        if cls._redis is None:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            cls.logger.debug(f"Connecting to Redis at {host}:{port}")
            cls._redis = Redis(host, port, decode_responses=True)

    def names(self) -> List[str]:
        return self.__matcher.names()

    def _publish(self, key_name: str, data: Any):
        if self._redis is None:
            return
        buf = pickle.dumps(data)
        s = base64.b64encode(buf)
        self._redis.lpush(key_name, s)

    def _publish_colors(self, colors: List[ColorMatched]):
        if self._redis is None:
            return

        now_crc = binascii.crc32(datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode('utf-8'))
        epoch = datetime.utcfromtimestamp(0)
        evt = {
            "user": self.request.headers.get("X-User") or self.request.query_params.get("user") or f"_{now_crc % 100}",
            "run": self.request.headers.get("X-Run") or self.request.query_params.get("run") or f"_{epoch}",
            "request": {
                "url": self.request.url.path,
                "query": dict(self.request.query_params),
                "headers": dict(self.request.headers)
            },
            "colors": colors
        }
        self._publish("color-match", evt)

    def match(self, name) -> List[ColorMatched]:
        res = self.__matcher.match(name)
        self._publish_colors(res)
        return res
