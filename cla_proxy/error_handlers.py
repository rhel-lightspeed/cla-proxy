from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


def cla_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """
    Exception handler for HTTPExceptions that formats errors in CLA-compatible format.

    Args:
        request: FastAPI request object
        exc: HTTPException that was raised

    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"errors": [{"status": exc.status_code, "detail": exc.detail}]},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(403, cla_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(408, cla_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(503, cla_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(504, cla_exception_handler)  # type: ignore[arg-type]
