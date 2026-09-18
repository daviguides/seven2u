"""Maps domain errors to HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.errors import NotFoundError, UpstreamError, ValidationError

_STATUS_BY_ERROR: dict[type[Exception], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    UpstreamError: status.HTTP_502_BAD_GATEWAY,
}


async def _domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    code = _STATUS_BY_ERROR[type(exc)]
    return JSONResponse(status_code=code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """Attach one handler per domain error type."""
    for error_type in _STATUS_BY_ERROR:
        app.add_exception_handler(error_type, _domain_error_handler)
