# import asyncio
from datetime import datetime
import os
import socket
from typing import Annotated, Dict, List, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Query, status, Response, Request
from services.color_matcher_with_storage import ColorMatcherWithStorage
from services.color_matcher import ColorMatcher, ColorMatcherProtocol
from services.color_matcher_with_delay import ColorMatcherWithDelay
from services.schemas import MatchColorRequest, ColorMatched, ColorListResponse, ColorNamesResponse
from logger_factory import get_logger, min_log_level, log_config


boot_time = datetime.now()
host_name = socket.gethostname()
logger = get_logger(__name__)

app = FastAPI(
    title="Color API for DevOps Testing",
    description=(
        "Use this container to test OpenTofu or Pulumi deployment templates. "
    ),
    version="1.0.0"
)


@app.get("/")
@app.get("/color/ping")
async def health_check() -> Dict[str, Any]:
    current_time = datetime.now()
    resp = {
        "status": "OK",
        "name": "color api",
        "host": host_name,
        "boot": boot_time,
        "alive": str(current_time - boot_time)
    }
    logger.debug("Health check: OK for %s", host_name)
    return resp


def resolve_color_matcher(req: Request) -> ColorMatcherProtocol:
    return ColorMatcherWithDelay(ColorMatcherWithStorage(ColorMatcher(), req))  # decorator pattern


@app.get("/color/match", response_model=ColorListResponse)
async def match_color(
    query: Annotated[MatchColorRequest, Query()], request: Request, response: Response
) -> ColorListResponse:
    if not query.name.strip():
        raise HTTPException(status_code=400, detail="The 'name' field cannot be empty.")

    matcher: ColorMatcherProtocol = resolve_color_matcher(request)
    results: List[ColorMatched] = matcher.match(query.name)
    if results is None or len(results) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
    return ColorListResponse(inquery=query, count=len(results), matches=results)


@app.get("/color/names", response_model=ColorNamesResponse)
async def list_names(request: Request) -> ColorNamesResponse:
    matcher: ColorMatcherProtocol = resolve_color_matcher(request)
    names = matcher.names()
    return ColorNamesResponse(count=len(names), names=names)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    kargs = {
        "host": host,
        "port": int(port),
        "log_level": min_log_level()
    }
    fmt = log_config()
    if fmt is not None:
        kargs["log_config"] = fmt
    uvicorn.run(app, **kargs)  # type: ignore
