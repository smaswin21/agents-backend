"""User Service - Business logic for user operations."""
from typing import Optional
from db.models import create_document, get_document, find_documents, COLLECTIONS
from schemas.user import UserCreate, UserResponse


async def create_user(user_data: UserCreate) -> str:
    """Create a new user."""
    data = user_data.model_dump(exclude_unset=True)
    user_id = await create_document(COLLECTIONS["users"], data)
    return user_id


async def get_user(user_id: str) -> Optional[UserResponse]:
    """Get a user by ID."""
    doc = await get_document(COLLECTIONS["users"], user_id)
    if not doc:
        return None
    return UserResponse(**doc)


async def get_users_by_household(household_id: str) -> list[UserResponse]:
    """Get all users in a household."""
    docs = await find_documents(COLLECTIONS["users"], {"household_id": household_id})
    return [UserResponse(**doc) for doc in docs]