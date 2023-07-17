import typing as t

from starlette.middleware import Middleware

from ellar.common.helper import build_init_kwargs
from ellar.common.types import ASGIApp
from ellar.di import EllarInjector, injectable

T = t.TypeVar("T")


class EllarMiddleware(Middleware):
    def __init__(self, cls: type, **options: t.Any) -> None:
        super().__init__(cls, **options)
        injectable()(self.cls)
        self.options = build_init_kwargs(self.cls, self.options)

    def __call__(self, app: ASGIApp, injector: EllarInjector) -> T:
        self.options.update(app=app)
        return injector.create_object(self.cls, additional_kwargs=self.options)