import typing as t

from injector import ConstructorOrClassT, inject

from architek.constants import INJECTABLE_ATTRIBUTE
from architek.exceptions import ImproperConfiguration
from architek.shortcuts import fail_silently
from architek.types import T

from .injector import Container
from .scopes import DIScope, ScopeDecorator, SingletonScope

__all__ = ("ProviderConfig", "injectable", "is_decorated_with_injectable", "get_scope")


class ProviderConfig(t.Generic[T]):
    __slots__ = ("base_type", "use_value", "use_class")

    def __init__(
        self,
        base_type: t.Union[t.Type[T], t.Type],
        *,
        use_value: t.Optional[T] = None,
        use_class: t.Optional[t.Type[T]] = None
    ):
        if use_value and use_class:
            raise ImproperConfiguration(
                "`use_class` and `use_value` can not be used at the same time."
            )

        self.base_type = base_type
        self.use_value = use_value
        self.use_class = use_class

    def register(self, container: Container) -> None:
        scope = get_scope(self.base_type) or SingletonScope
        if self.use_class:
            scope = get_scope(self.use_class) or SingletonScope
            container.register(
                base_type=self.base_type, concrete_type=self.use_class, scope=scope
            )
        elif self.use_value:
            container.add_singleton(
                base_type=self.base_type, concrete_type=self.use_value
            )
        else:
            container.register(base_type=self.base_type, scope=scope)


class _Injectable:
    def __init__(
        self, scope: t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]] = None
    ) -> None:
        self.scope = scope or SingletonScope

    def __call__(self, func_or_class: ConstructorOrClassT) -> ConstructorOrClassT:
        fail_silently(inject, constructor_or_class=func_or_class)
        setattr(func_or_class, INJECTABLE_ATTRIBUTE, self.scope)
        return func_or_class


def injectable(
    scope: t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]] = SingletonScope
) -> t.Union[ConstructorOrClassT, t.Callable]:
    """Decorates a callable or Type with inject and Defines Type or callable scope injection scope

    Example use:

    >>> @injectable # default is 'singleton_scope'
    ... class InjectableType2:
    ...     def __init__(self):
    ...         pass
    >>>
    >>> @injectable(scope=request_scope)
    ... class InjectableType3:
    ...     def __init__(self):
    ...         pass
    """
    if (
        isinstance(scope, ScopeDecorator)
        or isinstance(scope, type)
        and issubclass(scope, DIScope)
    ):
        return _Injectable(scope)
    return _Injectable()(t.cast(ConstructorOrClassT, scope))


def is_decorated_with_injectable(func_or_class: ConstructorOrClassT) -> bool:
    """See if given Type or Call is declared with a scope.

    Example use:
    >>> class NonInjectableType:
    ...     def __init__(self):
    ...         pass

    >>> @injectable
    ... class InjectableType2:
    ...     def __init__(self):
    ...         pass

    >>> is_decorated_with_injectable(NonInjectableType)
    True
    >>>
    >>> is_decorated_with_injectable(InjectableType2)
    True
    """
    return hasattr(func_or_class, INJECTABLE_ATTRIBUTE)


def get_scope(
    func_or_class: ConstructorOrClassT,
) -> t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]]:
    """Get scope declared scope if available in a type or callable"""
    return t.cast(
        t.Optional[t.Union[t.Type[DIScope], ScopeDecorator]],
        getattr(
            func_or_class,
            INJECTABLE_ATTRIBUTE,
            getattr(func_or_class, "__scope__", None),
        ),
    )
