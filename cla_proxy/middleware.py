from fastapi import Request
from starlette.status import HTTP_504_GATEWAY_TIMEOUT
from fastapi.responses import JSONResponse
from typing import Callable
import asyncio


async def timeout_middleware(request: Request, call_next: Callable) -> JSONResponse:
    """
    Middleware for handling timeouts from requests.

    Sometimes watsonx is _really slow_ to respond and we need to catch these gracefully.
    """
    err_msg = "There was a problem while generating an answer. Please try again."
    try:
        return await asyncio.wait_for(
            call_next(request), timeout=request.app.state.config.backend.timeout
        )

    except asyncio.TimeoutError:
        return JSONResponse(
            {"data": {"text": err_msg}}, status_code=HTTP_504_GATEWAY_TIMEOUT
        )
