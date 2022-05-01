import importlib
import typing as t

from starlette.config import environ

from ellar.compatible.dict import (
    AttributeDictAccessMixin,
    DataMapper,
    DataMutableMapper,
)
from ellar.constants import ELLAR_CONFIG_MODULE
from ellar.types import VT

from . import default_settings
from .app_settings_models import ArchitekConfig


class _ConfigState(DataMutableMapper):
    pass


_config_state = _ConfigState()


class Config(DataMapper, AttributeDictAccessMixin):
    _data: _ConfigState
    __slots__ = ("config_module",)

    def __init__(
        self,
        config_state: _ConfigState = _config_state,
        **mapping: t.Any,
    ):
        """
        Creates a new instance of Configuration object with the given values.
        """
        super().__init__()
        self.config_module = environ.get(ELLAR_CONFIG_MODULE, None)
        if "app_configured" not in config_state:
            config_state.clear()
            for setting in dir(default_settings):
                if setting.isupper():
                    config_state[setting] = getattr(default_settings, setting)

            if self.config_module:
                mod = importlib.import_module(self.config_module)
                for setting in dir(mod):
                    if setting.isupper():
                        config_state[setting] = getattr(mod, setting)

        config_state.update(**mapping)

        self._data: _ConfigState = config_state
        validate_config = ArchitekConfig.parse_obj(self._data)
        self._data.update(validate_config.serialize())

    def set_defaults(self, **kwargs: t.Any) -> "Config":
        for k, v in kwargs.items():
            self._data.setdefault(k, v)
        return self

    @classmethod
    def add_value(cls, **kwargs: t.Any) -> t.Type["Config"]:
        for k, v in kwargs.items():
            setattr(default_settings, k, v)
        return cls

    @classmethod
    def get_value(cls, key: t.Any) -> t.Any:
        return getattr(default_settings, key, None)

    def __repr__(self) -> str:
        hidden_values = {key: "..." for key in self._data.keys()}
        return f"<Configuration {repr(hidden_values)}, settings_module: {self.config_module}>"

    @property
    def values(self) -> t.ValuesView[VT]:
        """
        Returns a copy of the dictionary of current settings.
        """
        return self._data.values()