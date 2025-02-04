from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any, Dict, List, Protocol, Tuple
from services.schemas import ColorMatched
from logger_factory import get_logger


class ColorMatcherProtocol(Protocol):
    def names(self) -> List[str]:
        ...

    def match(self, name: str) -> List[ColorMatched]:
        ...


class ColorMatcherABC(ABC, ColorMatcherProtocol):
    @abstractmethod
    def names(self) -> List[str]:
        pass

    @abstractmethod
    def match(self, name: str) -> List[ColorMatched]:
        pass


class ColorMatcher(ColorMatcherABC):
    colors: Dict[str, Any] = {}
    hexmap: Dict[str, str] = {}
    re_color_num = re.compile(r"^\s*([a-z]{3,})\s*([0-9])\s*$", flags=re.IGNORECASE)
    re_color_mod = re.compile(r"^\s*(light|mild|medium|standard|regular|dark)\s+([a-z]{3,})\s*$", flags=re.IGNORECASE)
    re_hex_name = re.compile(r"^\s*[#]?([a-f0-9]{6})\s*$", flags=re.IGNORECASE)
    re_short_hex_name = re.compile(r"^\s*[#]?([a-f0-9]{3})\s*$", flags=re.IGNORECASE)
    logger = get_logger(__name__)

    @classmethod
    def _load_colors(cls):
        if len(cls.colors) > 0:
            return

        # SEE: https://yeun.github.io/open-color/
        # get current script path:
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, "open_colors.json")
        with open(file_path, encoding="utf-8") as f:
            colors = json.load(f)
            cls.colors = colors

        for color_name, value in colors.items():
            if isinstance(value, str):
                # skip first character of value
                hex_key = value[1:].lower()
                cls.hexmap[hex_key] = color_name
            elif isinstance(value, list):
                index = 0
                for hex_value in value:
                    hex_value = hex_value[1:].lower()
                    cls.hexmap[hex_value] = f"{color_name}{index}"
                    index += 1

        cls.logger.debug("Loaded %d colors OK", len(cls.colors))

    def __init__(self):
        self._load_colors()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))  # type: ignore

    @staticmethod
    def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        return "#%02x%02x%02x" % rgb

    def names(self) -> List[str]:
        return list(self.colors.keys())

    def match(self, name: str) -> List[ColorMatched]:
        name = name.lower()
        results: List[ColorMatched] = []
        direct = self.colors.get(name)
        index_hint: int = -1

        if direct is None:  # no direct match, check short hex
            exp = self.re_short_hex_name.findall(name)
            if exp is not None and len(exp) >= 1 and isinstance(exp[0], str):
                hex_key = exp[0].lower()
                # expand short hex_key to long hex format
                name = f"#{hex_key[0] * 2}{hex_key[1] * 2}{hex_key[2] * 2}"

        if direct is None:  # no direct match, check hexmap
            exp = self.re_hex_name.findall(name)
            if exp is not None and len(exp) >= 1 and isinstance(exp[0], str):
                hex_key = exp[0].lower()
                color_name = self.hexmap.get(hex_key)
                if color_name is not None:
                    rgb = self._hex_to_rgb(hex_key)
                    m = ColorMatched(name=color_name, hex=f"#{hex_key}", r=rgb[0], g=rgb[1], b=rgb[2])
                    results.append(m)
                    self.logger.debug("Matched %s to %d colors", name, len(results))
                    return results  # return early because we're constructing the result directly

        if direct is None:  # no direct match, attempt to match with number
            exp = self.re_color_num.findall(name)
            if exp is not None and len(exp) >= 1 and len(exp[0]) == 2:
                base_name = exp[0][0]
                if base_name in self.colors:
                    direct = self.colors.get(base_name)
                    index_hint = int(exp[0][1])

        if direct is None:  # no direct match, attempt to match with modifier
            exp = self.re_color_mod.findall(name)
            if exp is not None and len(exp) >= 1 and len(exp[0]) == 2:
                base_name = exp[0][1]
                if base_name in self.colors:
                    direct = self.colors.get(base_name)
                    case = exp[0][0].lower()
                    if case == "light":
                        index_hint = 0
                    elif case == "mild":
                        index_hint = 2
                    elif case == "strong":
                        index_hint = 7
                    elif case == "dark":
                        index_hint = 9
                    else:
                        index_hint = 5

        # check if direct is a string or an array
        if isinstance(direct, str):
            rgb = self._hex_to_rgb(direct)
            m = ColorMatched(name=name, hex=direct, r=rgb[0], g=rgb[1], b=rgb[2])
            results.append(m)
        elif isinstance(direct, list):
            if index_hint >= 0 and index_hint < len(direct):
                hex_value = direct[index_hint]
                rgb = self._hex_to_rgb(hex_value)
                m = ColorMatched(name=f"{name}{index_hint}", hex=hex_value, r=rgb[0], g=rgb[1], b=rgb[2])
                results.append(m)
            else:  # add everything
                index = 0
                for hex_value in direct:
                    index += 1
                    rgb = self._hex_to_rgb(hex_value)
                    m = ColorMatched(name=f"{name}{index}", hex=hex_value, r=rgb[0], g=rgb[1], b=rgb[2])
                    results.append(m)

        self.logger.debug("Matched %s to %d colors", name, len(results))
        return results
