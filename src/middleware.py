import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    """Log one request and attach its request ID to the response."""
    request_id = uuid.uuid4().hex[:8]  # short random ID for THIS request
    request.state.request_id = request_id  # other code can read it from request.state
    started = time.perf_counter()  # start the timer BEFORE the endpoint runs

    try:
        response = await call_next(request)  # hand the request to FastAPI / the endpoint
    except Exception:
        # BLANK 1: log at ERROR with the request ID; add exc_info=____ to include the traceback
        logger.error("Unexpected failure: request_id=%s", request_id, exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},  # client sees no exception details
        )

    duration_ms = (time.perf_counter() - started) * 1000  # elapsed time AFTER the endpoint

    message = (
        f"request_id={request_id} {request.method} {request.url.path} "
        f"status={response.status_code} duration={duration_ms:.1f}ms"
    )

    # BLANK 2: which status threshold means a server error (5xx)?
    if response.status_code >= 500:
        logger.error(message)
    # BLANK 3: which threshold starts client errors (4xx)?
    elif response.status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)  # BLANK 4: which level for successful responses?

    response.headers["X-Request-ID"] = request_id  # header, NOT part of the JSON body
    return response
