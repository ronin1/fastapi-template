import asyncio
from datetime import datetime
from logging import Logger
import os
import socket
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI
from logger_factory import get_logger, min_log_level, log_config
from services.color_consumer import ColorConsumer


_boot_time = datetime.now()
_host_name = socket.gethostname()  # pylint: disable=R0801


app = FastAPI(
    title="Color Worker App",
    description=(
        "Worker process that consumes data from Redis list & writes to Postgres table."
    ),
    version="1.0.0"
)


def log() -> Logger:
    if not hasattr(app, "logger"):
        app.logger = get_logger(__name__)  # type: ignore
    return app.logger  # type: ignore


@app.get("/")
@app.get("/worker")
async def health_check() -> Dict[str, Any]:
    current_time = datetime.now()
    resp = {
        "status": "OK",
        "name": "color worker 🤖",
        "host": _host_name,
        "boot": _boot_time,
        "alive": str(current_time - _boot_time)
    }
    log().debug("Health check: OK for %s", _host_name)
    return resp


def _api_setup() -> uvicorn.Server:
    host = os.getenv("HOST", os.getenv("WORKER_HOST", "0.0.0.0"))
    port = os.getenv("PORT", os.getenv("WORKER_PORT", "8000"))
    fmt = log_config()
    cfg: uvicorn.Config | None = None
    if fmt is not None:
        cfg = uvicorn.Config(
            app, host=host, port=int(port), log_level=min_log_level(), log_config=fmt)
    else:
        cfg = uvicorn.Config(app, host=host, port=int(port), log_level=min_log_level())
    svr = uvicorn.Server(cfg)
    return svr


async def main() -> None:
    try:
        svr = _api_setup()  # configure API server
        consumer = ColorConsumer()  # setup consumer
        worker_threads = int(os.getenv("WORKER_THREADS", "2")) or 0
        if worker_threads < 1:
            worker_threads = 1
        for _ in range(worker_threads):
            asyncio.create_task(consumer.pull_event_loop())  # fork consumer on a side loops

        await svr.serve()  # start API server. This is ablocking call on the main thread
        await consumer.cleanup()  # once the API server is closed, this statement will run
    except Exception as e:  # pylint: disable=broad-except
        log().error("Worker fault: %s", e)
        raise e
    finally:
        log().info("Worker exiting. Good bye 👋")


# SEE: https://stackoverflow.com/questions/76142431/how-to-run-another-application-within-the-same-running-event-loop  # noqa pylint: disable=line-too-long
if __name__ == "__main__":
    asyncio.run(main())
