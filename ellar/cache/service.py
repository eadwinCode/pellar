import typing as t

from ellar.di import injectable

from .backends.local_cache import LocalMemCacheBackend
from .interface import ICacheService, ICacheServiceSync
from .model import BaseCacheBackend


class InvalidCacheBackendKeyException(Exception):
    pass


class _CacheServiceSync(ICacheServiceSync):
    get_backend: t.Callable[..., BaseCacheBackend]

    def get(self, key: str, version: str = None, backend: str = None) -> t.Any:
        _backend = self.get_backend(backend)
        return _backend.get(key, version=version)

    def delete(self, key: str, version: str = None, backend: str = None) -> bool:
        _backend = self.get_backend(backend)
        return _backend.delete(key, version=version)

    def set(
        self,
        key: str,
        value: t.Any,
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return _backend.set(key, value, version=version, timeout=timeout)

    def touch(
        self,
        key: str,
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return _backend.touch(key, version=version, timeout=timeout)

    def has_key(self, key: str, version: str = None, backend: str = None) -> bool:
        _backend = self.get_backend(backend)
        return _backend.has_key(key, version=version)


@injectable  # type: ignore
class CacheService(_CacheServiceSync, ICacheService):
    """
    A Cache Backend Service that wraps Ellar cache backends
    """

    def __init__(self, backends: t.Dict[str, BaseCacheBackend] = None) -> None:
        if backends:
            assert backends.get(
                "default"
            ), "CACHES configuration must have a 'default' key."
        self._backends = backends or {
            "default": LocalMemCacheBackend(key_prefix="ellar", version=1, timeout=300)
        }

    def get_backend(self, backend: str = None) -> BaseCacheBackend:
        _backend = backend or "default"
        try:
            return self._backends[_backend]
        except KeyError:
            raise InvalidCacheBackendKeyException(
                f"There is no backend configured with the name: '{_backend}'"
            )

    async def get_async(
        self, key: str, version: str = None, backend: str = None
    ) -> t.Any:
        _backend = self.get_backend(backend)
        return await _backend.get_async(key, version=version)

    async def delete_async(
        self, key: str, version: str = None, backend: str = None
    ) -> bool:
        _backend = self.get_backend(backend)
        return bool(await _backend.delete_async(key, version=version))

    async def set_async(
        self,
        key: str,
        value: t.Any,
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return await _backend.set_async(key, value, timeout=timeout, version=version)

    async def touch_async(
        self,
        key: str,
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return await _backend.touch_async(key, timeout=timeout, version=version)

    async def has_key_async(
        self, key: str, version: str = None, backend: str = None
    ) -> bool:
        _backend = self.get_backend(backend)
        return await _backend.has_key_async(key, version=version)