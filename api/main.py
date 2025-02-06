from datetime import datetime
from logging import Logger
import os
import socket
from typing import Annotated, Dict, List, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Query, status, Response, Request
from services.color_matcher_with_publisher import ColorMatcherWithPublisher
from services.color_matcher import ColorMatcher, ColorMatcherProtocol
from services.color_matcher_with_delay import ColorMatcherWithDelay
from services.api_schemas import (
    MatchColorRequest, ColorMatched, ColorListResponse, ColorNamesResponse
)
from logger_factory import get_logger, min_log_level, log_config


_boot_time = datetime.now()
_host_name = socket.gethostname()  # pylint: disable=R0801


app = FastAPI(
    title="Color API App",
    description=(
        "API app that takes http requests and publishes to a Redis list."
    ),
    version="1.0.0"
)

def log() -> Logger:
    if not hasattr(app, "logger"):
        app.logger = get_logger(__name__)  # type: ignore
    return app.logger  # type: ignore

@app.get("/")
@app.get("/color")
async def health_check() -> Dict[str, Any]:
    current_time = datetime.now()
    resp = {
        "status": "OK",
        "name": "color api 🎨",
        "host": _host_name,
        "boot": _boot_time,
        "alive": str(current_time - _boot_time)
    }
    log().debug("Health check: OK for %s", _host_name)
    return resp


def _resolve_color_matcher(req: Request) -> ColorMatcherProtocol:
    return ColorMatcherWithDelay(
        ColorMatcherWithPublisher(ColorMatcher(), req)
    )  # decorator pattern


@app.get("/color/match", response_model=ColorListResponse)
async def match_color(
    query: Annotated[MatchColorRequest, Query()], request: Request, response: Response
) -> ColorListResponse:
    if not query.name.strip():
        raise HTTPException(status_code=400, detail="The 'name' field cannot be empty.")

    matcher: ColorMatcherProtocol = _resolve_color_matcher(request)
    results: List[ColorMatched] = matcher.match(query.name)
    if results is None or len(results) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
    return ColorListResponse(inquery=query, count=len(results), matches=results)


@app.get("/color/names", response_model=ColorNamesResponse)
async def list_names(request: Request) -> ColorNamesResponse:
    matcher: ColorMatcherProtocol = _resolve_color_matcher(request)
    names = matcher.names()
    return ColorNamesResponse(count=len(names), names=names)


def main() -> None:
    try:
        host = os.getenv("HOST", os.getenv("API_HOST", "0.0.0.0"))
        port = os.getenv("PORT", os.getenv("API_PORT", "8000"))
        kargs = {
            "host": host,
            "port": int(port),
            "log_level": min_log_level()
        }
        fmt = log_config()
        if fmt is not None:
            kargs["log_config"] = fmt

        # this is a blocking call and will only continue if the server is shutdown
        uvicorn.run(app, **kargs)  # type: ignore
    except Exception as e:  # pylint: disable=broad-except
        log().error("API server failed to start: %s", e)
        raise e
    finally:
        log().info("API server exiting. Good bye 🖖")


if __name__ == "__main__":
    main()
