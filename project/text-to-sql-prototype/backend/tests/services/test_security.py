"""Tests for security service."""
import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    encrypt_api_key,
    decrypt_api_key,
)


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_password_hashing(self):
        """Test that passwords can be hashed and verified."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        """Test that wrong password fails verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_hashing_is_consistent(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Test handling of empty password."""
        password = ""
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_long_password(self):
        """Test handling of long password (bcrypt has 72 byte limit)."""
        password = "a" * 100
        hashed = get_password_hash(password)

        # Should still work due to truncation handling
        assert verify_password(password, hashed) is True

    def test_unicode_password(self):
        """Test handling of unicode passwords."""
        password = "测试密码123!@#"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("different", hashed) is False


class TestAPIKeyEncryption:
    """Tests for API key encryption functionality."""

    def test_encrypt_decrypt_api_key(self):
        """Test that API keys can be encrypted and decrypted."""
        api_key = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(api_key)

        assert encrypted != api_key
        assert isinstance(encrypted, str)

        decrypted = decrypt_api_key(encrypted)
        assert decrypted == api_key

    def test_encryption_produces_different_results(self):
        """Test that encrypting same key produces different ciphertexts."""
        api_key = "sk-test-api-key-12345"
        encrypted1 = encrypt_api_key(api_key)
        encrypted2 = encrypt_api_key(api_key)

        # Due to Fernet's use of unique IVs, same plaintext produces different ciphertexts
        assert encrypted1 != encrypted2

        # But both decrypt to the same value
        assert decrypt_api_key(encrypted1) == api_key
        assert decrypt_api_key(encrypted2) == api_key

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        api_key = ""
        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)

        assert decrypted == api_key

    def test_encrypt_unicode(self):
        """Test encryption of unicode API key."""
        api_key = "密钥-测试-12345"
        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)

        assert decrypted == api_key

    def test_decrypt_invalid_data(self):
        """Test that decrypting invalid data raises an error."""
        with pytest.raises(Exception):
            decrypt_api_key("invalid-encrypted-data")
