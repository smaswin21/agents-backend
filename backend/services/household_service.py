"""Household Service - Business logic for household operations."""
from typing import Optional
from db.models import create_document, get_document, COLLECTIONS
from schemas.household import HouseholdCreate, HouseholdResponse


async def create_household(household_data: HouseholdCreate) -> str:
    """Create a new household."""
    data = household_data.model_dump(exclude_unset=True)
    # Remove owner_email from household data (will be used to create user)
    owner_email = data.pop("owner_email", None)
    household_id = await create_document(COLLECTIONS["households"], data)
    return household_id


async def get_household(household_id: str) -> Optional[HouseholdResponse]:
    """Get a household by ID."""
    doc = await get_document(COLLECTIONS["households"], household_id)
    if not doc:
        return None
    return HouseholdResponse(**doc)