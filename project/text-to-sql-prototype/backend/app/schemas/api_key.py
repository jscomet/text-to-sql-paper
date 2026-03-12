"""API key schemas for request and response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class APIKeyBase(BaseModel):
    """Base API key schema with common attributes."""
    key_type: str = Field(..., min_length=1, max_length=50, description="Provider type (openai, dashscope, etc.)")
    description: Optional[str] = Field(None, max_length=200, description="Optional description for the key")
    is_default: bool = Field(False, description="Whether this is the default key for the provider")


class APIKeyCreate(APIKeyBase):
    """Schema for creating a new API key."""
    key: str = Field(..., min_length=1, description="The actual API key (will be encrypted)")


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    description: Optional[str] = Field(None, max_length=200)
    is_default: Optional[bool] = None


class APIKeyInDB(APIKeyBase):
    """Schema for API key as stored in database."""
    id: int
    user_id: int
    key_encrypted: str = Field(..., description="Encrypted API key")
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class APIKeyResponse(BaseModel):
    """Schema for API key response (without exposing the actual key)."""
    id: int
    key_type: str
    description: Optional[str] = None
    is_default: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Schema for list of API keys response."""
    items: list[APIKeyResponse]
    total: int


class APIKeyDecryptRequest(BaseModel):
    """Schema for requesting decrypted API key (for internal use)."""
    pass


class APIKeyDecryptResponse(BaseModel):
    """Schema for decrypted API key response (internal use only)."""
    key: str
