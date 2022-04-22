import typing as t

from starlette.concurrency import run_in_threadpool

from architek.core.context import ExecutionContext
from architek.core.exceptions import RequestValidationError
from architek.core.routing.route import RouteOperation

from .base import ControllerRouteOperationBase


class ControllerRouteOperation(ControllerRouteOperationBase, RouteOperation):
    async def _handle(self, context: ExecutionContext) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)

        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)

        if self._is_coroutine:
            response_obj = await self.endpoint(controller_instance, **func_kwargs)
        else:
            response_obj = await run_in_threadpool(
                self.endpoint, controller_instance, **func_kwargs
            )
        response = self.response_model.process_response(
            ctx=context, response_obj=response_obj
        )
        await response(context.scope, context.receive, context.send)