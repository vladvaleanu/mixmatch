"""Forma unică a erorilor API: {"error": {"code": "...", "message": "..."}}."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorBody(BaseModel):
    error: ErrorDetail


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def error_response(status: int, code: str, message: str) -> JSONResponse:
    body = ErrorBody(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status, content=body.model_dump())


def responses(*statuses: int) -> dict[int | str, dict[str, object]]:
    """Documentează în OpenAPI erorile pe care le poate întoarce o rută."""
    return {status: {"model": ErrorBody} for status in statuses}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()))
        return error_response(422, "invalid_request", f"{where}: {first.get('msg', 'invalid')}")

    @app.exception_handler(HTTPException)
    async def _http(_request: Request, exc: HTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else f"http_{exc.status_code}"
        return error_response(exc.status_code, code, str(exc.detail))
