import typing as t

from starlette import status
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
    WebSocketException as StarletteWebSocketException,
)
from starlette.responses import PlainTextResponse, Response

from ellar.core.context import IExecutionContext
from ellar.core.exceptions import APIException, RequestValidationError
from ellar.serializer import serialize_object

from .interfaces import IExceptionHandler


class HTTPExceptionHandler(IExceptionHandler):
    exception_type_or_code = StarletteHTTPException

    async def catch(
        self, ctx: IExecutionContext, exc: StarletteHTTPException
    ) -> t.Union[Response, t.Any]:
        if exc.status_code in {204, 304}:
            return Response(status_code=exc.status_code, headers=exc.headers)
        return PlainTextResponse(
            exc.detail, status_code=exc.status_code, headers=exc.headers
        )


class WebSocketExceptionHandler(IExceptionHandler):
    exception_type_or_code = StarletteWebSocketException

    async def catch(
        self, ctx: IExecutionContext, exc: StarletteWebSocketException
    ) -> t.Union[Response, t.Any]:
        websocket = ctx.switch_to_websocket()
        await websocket.close(code=exc.code, reason=exc.reason)
        return None


class APIExceptionHandler(IExceptionHandler):
    exception_type_or_code = APIException

    async def catch(
        self, ctx: IExecutionContext, exc: APIException
    ) -> t.Union[Response, t.Any]:
        config = ctx.get_app().config
        headers = getattr(exc, "headers", {})
        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {"detail": exc.detail}
        return config.DEFAULT_JSON_CLASS(
            serialize_object(data), status_code=exc.status_code, headers=headers
        )


class RequestValidationErrorHandler(IExceptionHandler):
    exception_type_or_code = RequestValidationError

    async def catch(
        self, ctx: IExecutionContext, exc: RequestValidationError
    ) -> t.Union[Response, t.Any]:
        config = ctx.get_app().config
        return config.DEFAULT_JSON_CLASS(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": serialize_object(exc.errors())},
        )
