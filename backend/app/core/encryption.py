"""
KAIROS CDS — Field-level AES-256-GCM encryption for sensitive data.

Provides transparent encrypt/decrypt for PII fields in SQLAlchemy models.
If FIELD_ENCRYPTION_KEY is not set, fields are stored in plaintext (dev mode).
"""

import base64
import logging
import os
from typing import Optional

logger = logging.getLogger("kairos.encryption")

_ENCRYPTION_PREFIX = "ENC:"


def _get_key() -> Optional[bytes]:
    """Get the 32-byte encryption key from config."""
    from ..config import FIELD_ENCRYPTION_KEY
    if not FIELD_ENCRYPTION_KEY:
        return None
    try:
        key = base64.b64decode(FIELD_ENCRYPTION_KEY)
        if len(key) != 32:
            logger.error("FIELD_ENCRYPTION_KEY must be 32 bytes (base64-encoded)")
            return None
        return key
    except Exception:
        logger.error("Invalid FIELD_ENCRYPTION_KEY (must be valid base64)")
        return None


def is_encryption_active() -> bool:
    """Check if field encryption is properly configured."""
    return _get_key() is not None


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value using AES-256-GCM.
    Returns prefixed ciphertext or plaintext if encryption is not configured."""
    if not plaintext:
        return plaintext

    key = _get_key()
    if key is None:
        return plaintext

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Format: ENC:<base64(nonce + ciphertext)>
        payload = base64.b64encode(nonce + ct).decode("ascii")
        return f"{_ENCRYPTION_PREFIX}{payload}"
    except ImportError:
        logger.warning("cryptography package not installed, storing plaintext")
        return plaintext
    except Exception as e:
        logger.error("Encryption failed: %s", e)
        return plaintext


def decrypt_value(stored: str) -> str:
    """Decrypt an AES-256-GCM encrypted value.
    Handles both encrypted (ENC: prefix) and plaintext values."""
    if not stored or not stored.startswith(_ENCRYPTION_PREFIX):
        return stored  # Not encrypted, return as-is

    key = _get_key()
    if key is None:
        logger.warning("Cannot decrypt: FIELD_ENCRYPTION_KEY not set")
        return stored

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        payload = base64.b64decode(stored[len(_ENCRYPTION_PREFIX):])
        nonce = payload[:12]
        ct = payload[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ct, None)
        return plaintext.decode("utf-8")
    except ImportError:
        logger.warning("cryptography package not installed, cannot decrypt")
        return stored
    except Exception as e:
        logger.error("Decryption failed: %s", e)
        return stored


# ── SQLAlchemy TypeDecorator for transparent field encryption ──

from sqlalchemy import TypeDecorator, String


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts string values.

    Usage:
        class Patient(Base):
            phone = Column(EncryptedString(255), nullable=True)
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_value(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_value(value)
