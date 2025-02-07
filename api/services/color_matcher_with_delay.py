import time
from datetime import datetime
import random
from typing import List
import os
from services.color_matcher import ColorMatcherABC
from services.api_schemas import ColorMatched
from logger_factory import get_logger


class ColorMatcherWithDelay(ColorMatcherABC):
    logger = get_logger(__name__)
    min_delay_ms: float = float(os.getenv("API_DELAY_MIN", "0"))
    max_delay_ms: float = float(os.getenv("API_DELAY_MAX", "0"))
    can_delay: bool = min_delay_ms >= 0 and max_delay_ms >= min_delay_ms and max_delay_ms > 0  # noqa pylint: disable=R1716
    is_random_delay: bool = can_delay and min_delay_ms < max_delay_ms

    def __init__(self, matcher: ColorMatcherABC):
        self.__matcher = matcher
        self.logger.debug("ColorMatcherWithDelay initialized w/ can_delay: %s", self.can_delay)

    @classmethod
    def _delay(cls, start: datetime) -> None:
        if cls.can_delay:
            took_ms: float = (datetime.now() - start).microseconds / 1_000
            nap_ms: float = round(
                random.uniform(cls.min_delay_ms, cls.max_delay_ms) if cls.is_random_delay
                else cls.max_delay_ms, 2)
            cls.logger.debug("Execution took %sms Delaying for %fms", took_ms, nap_ms)
            time.sleep(nap_ms / 1_000)

    def names(self) -> List[str]:
        start = datetime.now()
        res = self.__matcher.names()
        self._delay(start)
        return res

    def match(self, name: str) -> List[ColorMatched]:
        start = datetime.now()
        res = self.__matcher.match(name)
        self._delay(start)
        return res
