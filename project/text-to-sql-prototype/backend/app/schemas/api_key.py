"""API key schemas for request and response validation."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# Valid format types for LLM responses
FormatType = Literal["openai", "anthropic", "vllm"]


class APIKeyBase(BaseModel):
    """Base API key schema with common attributes."""
    provider: str = Field(..., min_length=1, max_length=50, description="Provider name (deepseek, openai, etc.)")
    base_url: Optional[str] = Field(None, max_length=500, description="Custom base URL for the API")
    model: Optional[str] = Field(None, max_length=100, description="Model name (e.g., gpt-4, qwen-plus)")
    format_type: FormatType = Field(default="openai", description="API format: openai, anthropic, or vllm")
    description: Optional[str] = Field(None, max_length=200, description="Optional description for the key")
    is_default: bool = Field(False, description="Whether this is the default key for the provider")

    @field_validator("format_type")
    @classmethod
    def validate_format_type(cls, v: str) -> str:
        """Validate format type."""
        valid_types = ["openai", "anthropic", "vllm"]
        if v not in valid_types:
            raise ValueError(f"format_type must be one of: {', '.join(valid_types)}")
        return v


class APIKeyCreate(APIKeyBase):
    """Schema for creating a new API key."""
    key: str = Field(..., min_length=1, description="The actual API key (will be encrypted)")


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    base_url: Optional[str] = Field(None, max_length=500)
    model: Optional[str] = Field(None, max_length=100)
    format_type: Optional[FormatType] = None
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
    provider: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    format_type: str = "openai"
    description: Optional[str] = None
    is_default: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Schema for list of API keys response."""
    list: list[APIKeyResponse]
    pagination: dict = {"page": 1, "page_size": 100, "total": 0, "total_pages": 0}


class APIKeyDecryptRequest(BaseModel):
    """Schema for requesting decrypted API key (for internal use)."""
    pass


class APIKeyDecryptResponse(BaseModel):
    """Schema for decrypted API key response (internal use only)."""
    key: str
