
import os

from cryptography.fernet import Fernet
from django.db import models


class EncryptedTextField(models.TextField):
    """
    Encrypt private notes before saving them to SQLite
    and decrypt them when reading through Django.
    """

    prefix = "enc:"

    def get_cipher(self):
        key = os.environ.get("READING_LAB_FERNET_KEY")

        if not key:
            raise RuntimeError(
                "READING_LAB_FERNET_KEY is not configured"
            )

        return Fernet(key.encode())

    def get_prep_value(self, value):
        if value is None or value == "":
            return value

        value = str(value)

        encrypted = self.get_cipher().encrypt(
            value.encode("utf-8")
        )

        return self.prefix + encrypted.decode("utf-8")

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value

        if value.startswith(self.prefix):
            token = value[len(self.prefix):]

            return self.get_cipher().decrypt(
                token.encode("utf-8")
            ).decode("utf-8")

        # Temporarily support existing plaintext notes.
        return value
