import typing as t

from ellar.common.compatible import AttributeDictAccessMixin, DataMutableMapper


class Identity(DataMutableMapper, AttributeDictAccessMixin):
    """Represent the user's identity."""

    def __init__(self, auth_type: str = None, **kwargs: t.Any) -> None:
        kwargs.setdefault("id", kwargs.get("id", kwargs.get("sub")))
        kwargs.update(dict(_auth_type=auth_type))
        super().__init__(**kwargs)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.id)

    @property
    def issuer(self) -> str:
        return self.get("issuer", "")

    @property
    def auth_type(self) -> str:
        return str(self._auth_type)

    def __repr__(self) -> str:  # pragma: no cover
        return '<{0} id="{1}" auth_type="{2}" is_authenticated={3}>'.format(
            self.__class__.__name__, self.id, self.auth_type, self.is_authenticated
        )


class AnonymousIdentity(Identity):
    def __init__(self) -> None:
        super().__init__(id=None)