"""API key management routes."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.security import decrypt_api_key, encrypt_api_key
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyListResponse, APIKeyResponse

router = APIRouter(prefix="/keys", tags=["API Keys"])


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyListResponse:
    """Get list of API keys for the current user.

    Returns key metadata without exposing the actual API keys.

    Args:
        current_user: The currently authenticated user.
        db: Database session.

    Returns:
        List of API keys with metadata (excluding the actual key values).
    """
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id)
    )
    api_keys = result.scalars().all()

    items = [
        APIKeyResponse(
            id=key.id,
            key_type=key.key_type,
            description=key.description,
            is_default=key.is_default,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
        )
        for key in api_keys
    ]

    return APIKeyListResponse(items=items, total=len(items))


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Add a new API key.

    The API key will be encrypted before storage.

    Args:
        key_data: The API key data including the actual key.
        current_user: The currently authenticated user.
        db: Database session.

    Returns:
        The created API key metadata (without the actual key).

    Raises:
        HTTPException: If the key type is invalid.
    """
    # Validate key type
    valid_types = ["openai", "dashscope"]
    if key_data.key_type.lower() not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid key type. Must be one of: {', '.join(valid_types)}"
        )

    # If setting as default, unset other defaults for this type
    if key_data.is_default:
        await db.execute(
            select(APIKey)
            .where(
                APIKey.user_id == current_user.id,
                APIKey.key_type == key_data.key_type.lower(),
                APIKey.is_default == True
            )
        )
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == current_user.id,
                APIKey.key_type == key_data.key_type.lower(),
                APIKey.is_default == True
            )
        )
        existing_default = result.scalar_one_or_none()
        if existing_default:
            existing_default.is_default = False
            await db.flush()

    # Encrypt the API key
    encrypted_key = encrypt_api_key(key_data.key)

    # Create new API key
    new_key = APIKey(
        user_id=current_user.id,
        key_type=key_data.key_type.lower(),
        key_encrypted=encrypted_key,
        description=key_data.description,
        is_default=key_data.is_default,
    )

    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return APIKeyResponse(
        id=new_key.id,
        key_type=new_key.key_type,
        description=new_key.description,
        is_default=new_key.is_default,
        created_at=new_key.created_at,
        last_used_at=new_key.last_used_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an API key.

    Args:
        key_id: The ID of the API key to delete.
        current_user: The currently authenticated user.
        db: Database session.

    Raises:
        HTTPException: If the key is not found or doesn't belong to the user.
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    await db.delete(api_key)
    await db.commit()


async def get_user_api_key(
    user_id: int,
    key_type: str,
    db: AsyncSession,
    prefer_default: bool = True,
) -> str | None:
    """Get a user's API key for a specific provider.

    This is a helper function for internal use (not an endpoint).

    Args:
        user_id: The user ID.
        key_type: The provider type (openai, dashscope).
        db: Database session.
        prefer_default: Whether to prefer the default key.

    Returns:
        The decrypted API key, or None if not found.
    """
    key_type = key_type.lower()

    if prefer_default:
        # Try to get the default key first
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.key_type == key_type,
                APIKey.is_default == True
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key:
            return decrypt_api_key(api_key.key_encrypted)

    # Get any key for this type
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == user_id,
            APIKey.key_type == key_type
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key:
        return decrypt_api_key(api_key.key_encrypted)

    return None
