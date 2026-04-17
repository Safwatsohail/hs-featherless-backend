from __future__ import annotations

import base64
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken


class CryptoError(RuntimeError):
    pass


@dataclass(frozen=True)
class CryptoBox:
    fernet: Fernet

    @staticmethod
    def from_master_key(master_key: str) -> "CryptoBox":
        try:
            raw = master_key.encode("utf-8")
            decoded = base64.urlsafe_b64decode(raw)
            if len(decoded) != 32:
                raise ValueError("MASTER_KEY must decode to 32 bytes.")
            return CryptoBox(fernet=Fernet(raw))
        except Exception as exc:  # noqa: BLE001
            raise CryptoError("Invalid MASTER_KEY; expected Fernet key.") from exc

    def encrypt(self, plaintext: str) -> str:
        token = self.fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self.fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise CryptoError("Failed to decrypt value (InvalidToken).") from exc

