from typing import List, Optional
from pydantic import BaseModel, Field
from shared_schemas import ColorMatched

class MatchColorRequest(BaseModel):
    name: str = Field(
        ..., min_length=3, max_length=32, description="Provide a color name or hex code")

class RandomColorRequest(BaseModel):
    r: Optional[int] = Field(..., ge=0, le=255, description="Optional Red value")
    g: Optional[int] = Field(..., ge=0, le=255, description="Optional Green value")
    b: Optional[int] = Field(..., ge=0, le=255, description="Optional Blue value")

class ColorListResponse(BaseModel):
    inquery: MatchColorRequest | RandomColorRequest
    count: int = 0
    matches: List[ColorMatched]

class ColorNamesResponse(BaseModel):
    count: int = 0
    names: List[str]
