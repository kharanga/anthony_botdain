import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

SALT_LENGTH = 16
NONCE_LENGTH = 12
KEY_LENGTH = 32
SCRYPT_COST = 2**15
SCRYPT_BLOCK_SIZE = 8
SCRYPT_PARALLELISM = 1
KEY_CHECK_PLAINTEXT = b"travel-companion vault key check"


class WrongKey(Exception):
    pass


def new_salt() -> bytes:
    return os.urandom(SALT_LENGTH)


def key_from_pin(pin: str, salt: bytes) -> bytes:
    scrypt = Scrypt(salt=salt, length=KEY_LENGTH, n=SCRYPT_COST, r=SCRYPT_BLOCK_SIZE, p=SCRYPT_PARALLELISM)
    return scrypt.derive(pin.encode())


def seal(key: bytes, plaintext: bytes, purpose: bytes) -> bytes:
    nonce = os.urandom(NONCE_LENGTH)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, purpose)


def open_sealed(key: bytes, sealed: bytes, purpose: bytes) -> bytes:
    nonce, ciphertext = sealed[:NONCE_LENGTH], sealed[NONCE_LENGTH:]
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, purpose)
    except InvalidTag as error:
        raise WrongKey from error


def key_check_for(key: bytes) -> bytes:
    return seal(key, KEY_CHECK_PLAINTEXT, b"key-check")


def key_matches_check(key: bytes, key_check: bytes) -> bool:
    try:
        return open_sealed(key, key_check, b"key-check") == KEY_CHECK_PLAINTEXT
    except WrongKey:
        return False
