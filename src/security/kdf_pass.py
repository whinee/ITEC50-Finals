import os

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def get_kdf() -> Argon2id:
    return Argon2id(
        salt=os.urandom(16),
        length=32,
        iterations=1,
        lanes=4,
        memory_cost=64 * 1024,
        ad=None,
        secret=None,
    )
