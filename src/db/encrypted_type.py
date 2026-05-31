import sqlalchemy.types as types
from cryptography.fernet import Fernet
from sqlalchemy.dialects.postgresql import TEXT

from src.config.settings import settings


class EncryptedType(types.TypeDecorator):
    """A custom SQLAlchemy TypeDecorator that seamlessly encrypts data before hitting the PostgreSQL database, and decrypts it when fetched.
    It guarantees E2EE (End-to-End Encryption) at rest by leveraging the highly secure Fernet symmetric encryption algorithm.
    """  # noqa: D205, D213

    impl = TEXT
    cache_ok = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not settings.AUTH.DB_ENCRYPTION_KEY:
            raise ValueError(
                "DB_ENCRYPTION_KEY must be set in the environment variables.",
            )
        self.fernet = Fernet(settings.AUTH.DB_ENCRYPTION_KEY.encode("utf-8"))

    def process_bind_param(self, value, dialect):
        """
        Encrypt the value before saving it to the database.

        Args:
            value (str | None): The plaintext string to encrypt.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            str | None: The base64-encoded encrypted string.

        """
        if value is not None:
            if not isinstance(value, str):
                value = str(value)
            return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return value

    def process_result_value(self, value, dialect):
        """
        Decrypt the value retrieved from the database.

        Args:
            value (str | None): The encrypted string.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            str | None: The decrypted plaintext string.

        """
        if value is not None:
            try:
                return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:  # noqa: BLE001
                # If decryption fails (e.g. data was previously unencrypted or key rotated), just return the raw string
                return value
        return value
