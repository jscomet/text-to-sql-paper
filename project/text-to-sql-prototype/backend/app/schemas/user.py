"""User schemas for request and response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration request."""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user update request."""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login request."""
    username: str
    password: str


class UserInDB(UserBase):
    """Schema for user stored in database (includes password_hash)."""
    id: int
    password_hash: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    role: str
    status: str
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    """Schema for token response with user data."""
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: str  # subject (username)
    exp: datetime  # expiration time
