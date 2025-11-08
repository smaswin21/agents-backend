"""
Pantry schema definitions.
Represents inventory items and their par levels.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PantryItemBase(BaseModel):
    """Base pantry item fields."""
    household_id: str = Field(..., description="Household this item belongs to")
    item_name: str = Field(..., description="Name of the item")
    par_level: float = Field(..., ge=0, description="Minimum stock level before reorder")
    on_hand: float = Field(default=0, ge=0, description="Current quantity on hand")
    daily_rate: Optional[float] = Field(None, ge=0, description="Estimated daily consumption rate")
    lead_time_days: int = Field(default=1, ge=0, description="Days until delivery after order")
    preferred_brand: Optional[str] = None
    preferred_size: Optional[str] = None


class PantryItemCreate(PantryItemBase):
    """Schema for creating a pantry item."""
    pass


class PantryItemBulkCreate(BaseModel):
    """Schema for bulk creating pantry items."""
    household_id: str
    items: List[PantryItemCreate]


class PantryItemUpdate(BaseModel):
    """Schema for updating pantry item (partial updates)."""
    on_hand: Optional[float] = Field(None, ge=0)
    par_level: Optional[float] = Field(None, ge=0)
    daily_rate: Optional[float] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    preferred_brand: Optional[str] = None
    preferred_size: Optional[str] = None


class PantryItemResponse(PantryItemBase):
    """Schema for pantry item responses."""
    id: str = Field(..., alias="_id")
    is_low: bool = Field(..., description="Whether item is below par level")
    last_added_at: Optional[datetime] = Field(None, description="When item was last added to grocery list")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


# Feedback schemas
class ItemFeedbackCreate(BaseModel):
    """Schema for creating item feedback."""
    user_id: str
    status: str = Field(..., description="Status: 'fine', 'dwindling', or 'empty'")


class ItemFeedbackResponse(BaseModel):
    """Schema for item feedback responses."""
    id: str = Field(..., alias="_id")
    household_id: str
    item_id: str
    user_id: str
    status: str
    created_at: datetime

    class Config:
        populate_by_name = True