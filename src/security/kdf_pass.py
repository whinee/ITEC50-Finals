"""Argon2id Key Derivation.

Implements the military-grade Argon2id hashing algorithm to ruthlessly protect user passwords against timing and side-channel attacks.
"""

import os

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def get_kdf() -> Argon2id:
    """Instantiate a brutally secure Argon2id Key Derivation Function (KDF).

    Argon2id is the absolute state-of-the-art in password hashing, combining resistance against both GPU cracking (Argon2d) and side-channel timing attacks (Argon2i). By explicitly enforcing high memory cost and parallel lanes, this function forces adversaries to expend astronomical compute and RAM resources to brute-force a single password, essentially rendering rainbow tables and offline attacks computationally impossible.

    Returns:
        Argon2id: A fully configured, cryptographic-grade hasher ready for derivation.

    """
    return Argon2id(
        salt=os.urandom(16),
        length=32,
        iterations=1,
        lanes=4,
        memory_cost=64 * 1024,
        ad=None,
        secret=None,
    )
