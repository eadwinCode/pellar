import binascii
import typing as t
from abc import ABC
from base64 import b64decode

from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from architek.core.connection import HTTPConnection
from architek.exceptions import APIException, AuthenticationFailed

from .base import BaseHttpAuth, HTTPAuthorizationCredentials, HTTPBasicCredentials


class HttpBearerAuth(BaseHttpAuth, ABC):
    openapi_scheme: str = "bearer"
    openapi_bearer_format: t.Optional[str] = None
    header: str = "Authorization"

    @classmethod
    def get_guard_scheme(cls) -> t.Dict:
        scheme = super().get_guard_scheme()
        scheme.update(bearerFormat=cls.openapi_bearer_format)
        return scheme

    def _get_credentials(
        self, connection: HTTPConnection
    ) -> HTTPAuthorizationCredentials:
        authorization: str = connection.headers.get(self.header)
        scheme, _, credentials = self.authorization_partitioning(authorization)
        if not (authorization and scheme and credentials):
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        if scheme.lower() != self.openapi_scheme:
            raise APIException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
            )
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


class HttpBasicAuth(BaseHttpAuth, ABC):
    openapi_scheme: str = "basic"
    realm: t.Optional[str] = None
    header = "Authorization"

    def _not_unauthorized_exception(self, message: str) -> None:
        if self.realm:
            unauthorized_headers = {"WWW-Authenticate": f'Basic realm="{self.realm}"'}
        else:
            unauthorized_headers = {"WWW-Authenticate": "Basic"}
        raise AuthenticationFailed(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=message,
            headers=unauthorized_headers,
        )

    def _get_credentials(self, connection: HTTPConnection) -> HTTPBasicCredentials:
        authorization: str = connection.headers.get(self.header)
        scheme, _, credentials = self.authorization_partitioning(authorization)

        if (
            not (authorization and scheme and credentials)
            or scheme.lower() != self.openapi_scheme
        ):
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        data: t.Optional[t.Union[str, bytes]] = None
        try:
            data = b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            self._not_unauthorized_exception("Invalid authentication credentials")

        username, separator, password = (
            str(data).partition(":") if data else None,
            None,
            None,
        )
        if not separator:
            self._not_unauthorized_exception("Invalid authentication credentials")
        return HTTPBasicCredentials(username=username, password=password)


class HttpDigestAuth(HttpBearerAuth, ABC):
    openapi_scheme = "digest"
    header = "Authorization"
