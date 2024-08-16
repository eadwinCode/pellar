from ellar.common.params import add_default_resolver
from ellar.common.params.resolvers.system_parameters import ExecutionContextParameter

from .execution import ExecutionContext
from .factory import ExecutionContextFactory, HostContextFactory
from .host import HostContext
from .injector import config, current_injector, with_injector_context
from .request import HttpRequestConnectionContext, current_connection

__all__ = [
    "ExecutionContext",
    "HostContext",
    "ExecutionContextFactory",
    "HostContextFactory",
    "current_injector",
    "config",
    "HttpRequestConnectionContext",
    "current_connection",
    "with_injector_context",
]

add_default_resolver(ExecutionContext, ExecutionContextParameter)
