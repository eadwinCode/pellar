from architek.core.endpoints.params import Param, ParamTypes
from architek.core.routing import OperationDefinitions

from .params import (
    Body,
    Cookie,
    File,
    Form,
    Header,
    Path,
    Query,
    WsBody,
    cxt,
    provide,
    req,
    ws,
)

_route_definitions = OperationDefinitions()

Get = _route_definitions.get
Post = _route_definitions.post

Delete = _route_definitions.delete
Patch = _route_definitions.patch

Put = _route_definitions.put
Options = _route_definitions.options

Trace = _route_definitions.trace
Head = _route_definitions.head

HttpRoute = _route_definitions.http_route
WsRoute = _route_definitions.ws_route

__all__ = [
    "cxt",
    "provide",
    "req",
    "ws",
    "Body",
    "WsBody",
    "Cookie",
    "File",
    "Form",
    "Header",
    "Path",
    "Query",
    "Param",
    "ParamTypes",
    "Get",
    "Post",
    "Delete",
    "Patch",
    "Put",
    "Options",
    "Trace",
    "Head",
    "HttpRoute",
    "WsRoute",
]