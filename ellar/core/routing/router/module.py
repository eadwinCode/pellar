import typing as t

from starlette.routing import BaseRoute, Mount as StarletteMount, Route, Router
from starlette.types import ASGIApp

from ellar.compatible import AttributeDict
from ellar.constants import (
    CONTROLLER_METADATA,
    GUARDS_KEY,
    OPENAPI_KEY,
    OPERATION_HANDLER_KEY,
    VERSIONING_KEY,
)
from ellar.core.controller import ControllerBase
from ellar.core.routing.route import RouteOperation
from ellar.core.routing.websocket.route import WebsocketRouteOperation
from ellar.reflect import reflect

from ..operation_definitions import OperationDefinitions
from .route_collections import ModuleRouteCollection

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.guard import GuardCanActivate


__all__ = ["ModuleMount", "ModuleRouter", "controller_router_factory"]


def controller_router_factory(controller: t.Union[t.Type[ControllerBase], t.Any]) -> "ModuleMount":
    openapi = reflect.get_metadata(CONTROLLER_METADATA.OPENAPI, controller) or dict()
    routes = reflect.get_metadata(OPERATION_HANDLER_KEY, controller) or []
    app = Router()
    app.routes = ModuleRouteCollection(routes)  # type:ignore
    ss = reflect.get_metadata(CONTROLLER_METADATA.PATH, controller)
    router = ModuleMount(
        app=app,
        path=reflect.get_metadata(CONTROLLER_METADATA.PATH, controller),
        name=reflect.get_metadata(CONTROLLER_METADATA.NAME, controller),
        version=reflect.get_metadata(CONTROLLER_METADATA.VERSION, controller),
        guards=reflect.get_metadata(CONTROLLER_METADATA.GUARDS, controller),
        include_in_schema=reflect.get_metadata(
            CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, controller
        ),
        **openapi
    )
    return router


class ModuleMount(StarletteMount):
    def __init__(
        self,
        path: str,
        app: ASGIApp = None,
        routes: t.Sequence[BaseRoute] = None,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        include_in_schema: bool = False,
    ) -> None:
        super(ModuleMount, self).__init__(path=path, routes=routes, name=name, app=app)
        self.include_in_schema = include_in_schema
        self._meta: AttributeDict = AttributeDict(
            tag=tag or name or "Module Router",
            external_doc_description=external_doc_description,
            description=description,
            external_doc_url=external_doc_url,
        )
        self._route_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate", t.Any]
        ] = (guards or [])
        self._version = set(version or [])

    def get_meta(self) -> t.Mapping:
        return self._meta

    def get_tag(self) -> t.Dict:
        external_doc = None
        if self._meta.external_doc_url:
            external_doc = dict(
                url=self._meta.external_doc_url,
                description=self._meta.external_doc_description,
            )

        if self._meta.tag:
            return dict(
                name=self._meta.tag,
                description=self._meta.description,
                externalDocs=external_doc,
            )
        return dict()

    def _build_route_operation(self, route: RouteOperation) -> None:
        route.build_route_operation(
            path_prefix=self.path,
            name=self.name,
            include_in_schema=self.include_in_schema,
        )

    def _build_ws_route_operation(self, route: WebsocketRouteOperation) -> None:
        route.build_route_operation(path_prefix=self.path, name=self.name)

    def build_routes(self) -> t.List[BaseRoute]:
        for route in self.routes:
            _route: RouteOperation = t.cast("RouteOperation", route)

            route_versioning = reflect.get_metadata(VERSIONING_KEY, _route.endpoint)
            route_guards = reflect.get_metadata(GUARDS_KEY, _route.endpoint)
            openapi = (
                reflect.get_metadata(OPENAPI_KEY, _route.endpoint) or AttributeDict()
            )

            if not route_versioning:
                reflect.define_metadata(
                    VERSIONING_KEY, self._version, _route.endpoint, default_value=set()
                )
            if not route_guards:
                reflect.define_metadata(
                    GUARDS_KEY, self._route_guards, _route.endpoint, default_value=[]
                )

            if isinstance(_route, Route):
                if not openapi.tags and self._meta.get("tag"):
                    tags = {self._meta.get("tag")}
                    tags.update(set(openapi.tags or []))
                    openapi.update(tags=list(tags))
                    reflect.define_metadata(OPENAPI_KEY, openapi, _route.endpoint)
                self._build_route_operation(_route)
            elif isinstance(_route, WebsocketRouteOperation):
                self._build_ws_route_operation(_route)
        return list(self.routes)


class ModuleRouter(ModuleMount):
    operation_definition_class: t.Type[OperationDefinitions] = OperationDefinitions
    routes: ModuleRouteCollection  # type:ignore

    def __init__(
        self,
        path: str,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        include_in_schema: bool = True,
    ) -> None:
        app = Router()
        app.routes = ModuleRouteCollection()  # type:ignore

        super(ModuleRouter, self).__init__(
            path=path,
            tag=tag,
            name=name,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            version=version,
            guards=guards,
            include_in_schema=include_in_schema,
            app=app,
        )
        _route_definitions = self.operation_definition_class(t.cast(list, self.routes))

        self.Get = _route_definitions.get
        self.Post = _route_definitions.post

        self.Delete = _route_definitions.delete
        self.Patch = _route_definitions.patch

        self.Put = _route_definitions.put
        self.Options = _route_definitions.options

        self.Trace = _route_definitions.trace
        self.Head = _route_definitions.head

        self.HttpRoute = _route_definitions.http_route
        self.WsRoute = _route_definitions.ws_route
