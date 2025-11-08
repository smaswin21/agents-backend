"""
Grocery list schema definitions.
Represents weekly grocery lists and approval workflow.
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ListStatus(str, Enum):
    """Grocery list status enum."""
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    COMPLETED = "completed"


class ListItem(BaseModel):
    """Individual item in a grocery list."""
    item_name: str
    quantity: float = Field(..., ge=0)
    brand: Optional[str] = None
    size: Optional[str] = None
    is_shared: bool = Field(default=True, description="Shared vs personal item")
    added_by_agent: str = Field(..., description="Which agent added this (pantry/grocery)")
    reason: Optional[str] = Field(None, max_length=140, description="Reason for buying (≤140 chars)")


class GroceryListBase(BaseModel):
    """Base grocery list fields."""
    household_id: str
    week_start: datetime = Field(..., description="Start of the week this list covers")


class GroceryListCreate(GroceryListBase):
    """Schema for creating a grocery list."""
    items: List[ListItem] = Field(default_factory=list)


class GroceryListUpdate(BaseModel):
    """Schema for updating a grocery list."""
    items: Optional[List[ListItem]] = None
    status: Optional[ListStatus] = None
    cart_link: Optional[str] = None
    agent_notes: Optional[str] = None
    cost_estimate: Optional[float] = None
    eta: Optional[str] = None


class GroceryListResponse(GroceryListBase):
    """Schema for grocery list responses."""
    id: str = Field(..., alias="_id")
    status: ListStatus
    items: List[ListItem]
    cart_link: Optional[str] = None
    agent_notes: Optional[str] = None
    cost_estimate: Optional[float] = None
    eta: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class GroceryListApproveResponse(BaseModel):
    """Response schema for approving a grocery list."""
    status: str
    eta: Optional[str] = None
    total: Optional[float] = None
    message: str