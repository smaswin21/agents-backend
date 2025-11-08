"""
Household schema definitions.
A household represents a shared living space with multiple roommates.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class HouseholdBase(BaseModel):
    """Base household fields."""
    name: str = Field(..., description="Household name")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    budget_weekly: float = Field(default=0.0, ge=0, description="Weekly grocery budget")
    cooldown_days: int = Field(default=2, ge=0, description="Days to wait before reordering same item")


class HouseholdCreate(HouseholdBase):
    """Schema for creating a new household."""
    owner_email: EmailStr = Field(..., description="Email of the owner")


class HouseholdResponse(HouseholdBase):
    """Schema for household responses."""
    id: str = Field(..., alias="_id", description="MongoDB document ID")
    owner_user_id: Optional[str] = Field(None, description="ID of the owner user")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True