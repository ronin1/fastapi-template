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


boot_time = datetime.now()
host_name = socket.gethostname()
logger = get_logger(__name__)

app = FastAPI(
    title="Color Worker for DevOps Testing",
    description=(
        "Use this container to test OpenTofu or Pulumi deployment templates. "
    ),
    version="1.0.0"
)

def log() -> Logger:
    if not hasattr(app, "logger"):
        app.logger = get_logger(__name__)
    return app.logger

@app.get("/")
@app.get("/worker")
async def health_check() -> Dict[str, Any]:
    current_time = datetime.now()
    resp = {
        "status": "OK",
        "name": "color worker",
        "host": host_name,
        "boot": boot_time,
        "alive": str(current_time - boot_time)
    }
    log().debug("Health check: OK for %s", host_name)
    return resp


async def main() -> None:
    # fork side loop
    consumer = ColorConsumer()
    asyncio.create_task(consumer.pull_loop())

    # setup blocking API service
    host = os.getenv("HOST", os.getenv("WORKER_HOST", "0.0.0.0"))
    port = os.getenv("PORT", os.getenv("WORKER_PORT", "8001"))
    kargs = {
        "host": host,
        "port": int(port),
        "log_level": min_log_level()
    }
    fmt = log_config()
    if fmt is not None:
        kargs["log_config"] = fmt
    cfg = uvicorn.Config(app, **kargs)
    svr = uvicorn.Server(cfg)
    await svr.serve()


# SEE: https://stackoverflow.com/questions/76142431/how-to-run-another-application-within-the-same-running-event-loop
if __name__ == "__main__":
    asyncio.run(main())
