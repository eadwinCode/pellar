import typing as t

from ellar.common.utils.crypto import get_random_string

from .argon2 import Argon2Hasher
from .base import BaseHasher, EncodingType
from .bcrypt import BCryptHasher, BCryptSHA256Hasher
from .md5 import MD5Hasher
from .pbkdf import PBKDF2Hasher, PBKDF2SHA1Hasher
from .scrypt import ScryptHasher

# This will never be a valid encoded hash
_UNUSABLE_PASSWORD_PREFIX = "!"
_UNUSABLE_PASSWORD_SUFFIX_LENGTH = (
    40  # number of random chars to add after UNUSABLE_PASSWORD_PREFIX
)
__HASHERS_DICT: t.Dict[str, t.Type["BaseHasher"]] = {}


def add_hasher(*hashers: t.Type["BaseHasher"]) -> None:
    for hasher in hashers:
        __HASHERS_DICT.update({hasher.algorithm: hasher})


def get_hasher(algorithm: str = "pbkdf2_sha256") -> "BaseHasher":
    try:
        hasher_type = __HASHERS_DICT[algorithm]
        return hasher_type()
    except KeyError as kex:
        raise ValueError(
            f"Unknown password hashing algorithm '{algorithm}'. "
            f"Please use `add_hasher` in `ellar.core.security.hashers` package to add implementation for '{algorithm}'"
        ) from kex


def identify_hasher(encoded: str) -> "BaseHasher":
    possible_hashers = [v for k, v in __HASHERS_DICT.items() if v.identity(encoded)]
    if possible_hashers:
        return possible_hashers[0]()
    raise ValueError("Unable to identify Hasher")


def is_password_usable(encoded: t.Optional[str]) -> bool:
    """
    Return True if this password wasn't generated by
    User.set_unusable_password(), i.e. make_password(None).
    """
    return encoded is None or not encoded.startswith(_UNUSABLE_PASSWORD_PREFIX)


def make_password(
    password: t.Optional[EncodingType],
    algorithm: str = "pbkdf2_sha256",
    salt: t.Optional[str] = None,
) -> str:
    """
    Turn a plain-text password into a hash for database storage

    Same as encode() but generate a new random salt. If password is None then
    return a concatenation of UNUSABLE_PASSWORD_PREFIX and a random string,
    which disallows logins. Additional random string reduces chances of gaining
    access to staff or superuser accounts. See ticket #20079 for more info.
    """
    if password is None:
        return _UNUSABLE_PASSWORD_PREFIX + get_random_string(
            _UNUSABLE_PASSWORD_SUFFIX_LENGTH
        )
    if not isinstance(password, (bytes, str)):
        raise TypeError(
            "Password must be a string or bytes, got %s." % type(password).__qualname__
        )

    hasher = get_hasher(algorithm)
    # Passlib includes salt in almost every hash
    return hasher.encode(password, salt=salt)


def check_password(
    password: EncodingType,
    encoded: str,
    setter: t.Optional[t.Callable[..., t.Any]] = None,
    preferred_algorithm: str = "pbkdf2_sha256",
) -> bool:
    """
    Return a boolean of whether the raw password matches the three
    part encoded digest.

    If setter is specified, it'll be called if a password hash needs to be updated
     or regenerated based on the `preferred_algorithm`
    """

    if password is None or not is_password_usable(encoded):
        return False

    preferred = get_hasher(preferred_algorithm)
    try:
        hasher = identify_hasher(encoded)
    except ValueError:
        # encoded is gibberish or uses a hasher that's no longer installed.
        return False

    hasher_changed = hasher.algorithm != preferred.algorithm
    must_update: bool = hasher_changed or preferred.must_update(encoded)
    is_correct: bool = hasher.verify(password, encoded)

    if setter and is_correct and must_update:
        setter(password)
    return is_correct


add_hasher(
    PBKDF2Hasher,
    PBKDF2SHA1Hasher,
    Argon2Hasher,
    BCryptSHA256Hasher,
    BCryptHasher,
    ScryptHasher,
    MD5Hasher,
)

__all__ = [
    "BaseHasher",
    "PBKDF2Hasher",
    "PBKDF2SHA1Hasher",
    "Argon2Hasher",
    "BCryptSHA256Hasher",
    "BCryptHasher",
    "ScryptHasher",
    "MD5Hasher",
    "make_password",
    "check_password",
    "is_password_usable",
    "get_hasher",
    "identify_hasher",
    "add_hasher",
]
