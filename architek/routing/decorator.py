import typing as t
from functools import partial

from architek.constants import NOT_SET
from architek.operation_meta import OperationMeta

if t.TYPE_CHECKING:
    from architek.guard import GuardCanActivate


def _operation_wrapper(
    meta_key: str, meta_value: t.Any, target: t.Union[t.Callable, t.Any]
) -> t.Union[t.Callable, t.Any]:
    _meta = getattr(target, "_meta", OperationMeta())
    _meta_values: t.Any = [meta_value]
    existing = _meta.get(meta_key)
    if existing:
        if isinstance(existing, (list, tuple)):
            _meta_values.extend(existing)
            if isinstance(existing, tuple):
                _meta_values = tuple(_meta_values)
        elif isinstance(existing, set):
            _meta_values.extend(existing)
            _meta_values = set(_meta_values)
        elif isinstance(existing, dict):
            _meta_values = dict(meta_value)
            _meta_values.update(existing)
    else:
        _meta_values = meta_value
    _meta.update({meta_key: _meta_values})
    setattr(target, "_meta", _meta)
    return target


def set_meta(meta_key: t.Any, meta_value: t.Optional[t.Any] = NOT_SET) -> t.Callable:
    if meta_value is NOT_SET:
        return partial(set_meta, meta_key)

    def _decorator(target: t.Union[t.Callable, t.Any]) -> t.Union[t.Callable, t.Any]:
        return _operation_wrapper(meta_key, meta_value, target)

    return _decorator


def guards(
    *_guards: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
) -> t.Callable:
    return set_meta("route_guards", _guards)


def version(*_version: str) -> t.Callable:
    return set_meta("route_versioning", set(_version))


def openapi(
    operation_id: t.Optional[str] = None,
    summary: t.Optional[str] = None,
    description: t.Optional[str] = None,
    tags: t.Optional[t.List[str]] = None,
    deprecated: t.Optional[bool] = None,
) -> t.Callable:
    return set_meta(
        "openapi",
        dict(
            operation_id=operation_id,
            summary=summary,
            description=description,
            deprecated=deprecated,
            tags=tags,
        ),
    )