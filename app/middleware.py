import logging
from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    if request.url.path.startswith("/") and len(request.url.path) > 1:
        ip = request.client.host
        logger.info(f"Visit to {request.url.path}: IP={ip}, Timestamp={datetime.now(UTC)}")

    return response
