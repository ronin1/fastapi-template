import os
import json
from typing import Dict, List
from locust import HttpUser, task


# SEE: https://locust.io
class ColorEndpoints(HttpUser):
    color_file = "api/services/open_colors.json"  # SEE: https://yeun.github.io/open-color/
    color_data: Dict[str, str | List[str]] = dict()
    color_names: List[str] = []
    _color_names_len: int = 0
    color_codes: List[str] = []
    _color_codes_len: int = 0

    @classmethod
    def _init(cls) -> None:
        if not cls.color_data:
            path_override = os.getenv("COLOR_FILE", "")
            if path_override:
                cls.color_file = path_override

            with open(cls.color_file, 'r', encoding='utf-8') as f:
                cls.color_data = json.load(f)
            if not cls.color_data:
                raise ValueError("No data found in color file")

            for color, data in cls.color_data.items():
                if not color or not data:
                    continue
                if isinstance(data, list) and len(data) >= 1:
                    cls.color_names.append(color)
                    mid = len(data) // 2
                    cls.color_codes.append(data[mid][1:])
                    # ix = 0
                    # for code in data:
                    #     if not code:
                    #         continue
                    #     cls.color_names.append(f"{color}{ix}")
                    #     cls.color_codes.append(code[1:])
                    #     ix += 1
                    #     continue  # only take the first code
                elif isinstance(data, str):
                    cls.color_names.append(color)
                    cls.color_codes.append(data[1:])

            cls._color_names_len = len(cls.color_names)
            cls._color_codes_len = len(cls.color_codes)

    def on_start(self) -> None:
        self._init()
        return super().on_start()

    @task
    def color_keys(self) -> None:
        self.client.get("/color/names")

    _name_index = 0

    @task
    def color_matches_name(self) -> None:
        name: str = self.color_names[self._name_index]
        self._name_index = (self._name_index + 1) % self._color_names_len
        self.client.get(f"/color/match?name={name}")

    _code_index = 0

    @task
    def color_matches_code(self) -> None:
        code: str = self.color_codes[self._code_index]
        self._code_index = (self._code_index + 1) % self._color_codes_len
        self.client.get(f"/color/match?name={code}")
