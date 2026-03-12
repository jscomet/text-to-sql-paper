"""Security utilities for password hashing and verification."""
from base64 import b64decode, b64encode

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import settings

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return pwd_context.verify(password_bytes, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return pwd_context.hash(password_bytes)


def _get_fernet() -> Fernet:
    """Get Fernet instance for API key encryption.

    Returns:
        Fernet instance initialized with the encryption key.
    """
    # Derive a 32-byte key from the configured key
    key = settings.api_key_encryption_key.encode('utf-8')
    # Use URL-safe base64 encoding for Fernet key
    import hashlib
    key_hash = hashlib.sha256(key).digest()
    fernet_key = b64encode(key_hash)
    return Fernet(fernet_key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage.

    Args:
        api_key: The plain text API key to encrypt.

    Returns:
        The encrypted API key as a base64-encoded string.
    """
    fernet = _get_fernet()
    encrypted = fernet.encrypt(api_key.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key.

    Args:
        encrypted_key: The encrypted API key.

    Returns:
        The decrypted plain text API key.
    """
    fernet = _get_fernet()
    decrypted = fernet.decrypt(encrypted_key.encode('utf-8'))
    return decrypted.decode('utf-8')
