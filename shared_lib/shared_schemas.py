from pydantic import BaseModel, Field


COLOR_LIST_NAME: str = "ColorListResponse"


class ColorMatched(BaseModel):
    name: str = Field(..., min_length=3, max_length=32, description="Official name of an Open Color")
    r: int
    g: int
    b: int
    hex: str = Field(..., min_length=6, max_length=7, description="Hex value of the color")
