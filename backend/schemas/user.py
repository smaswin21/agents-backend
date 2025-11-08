"""
User schema definitions.
Represents user accounts and profiles.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user fields."""
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str
    budget: Optional[float] = Field(default=100.0, ge=0, description="Monthly grocery budget")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0, description="Monthly grocery budget")


class UserResponse(UserBase):
    """Schema for user responses."""
    id: str = Field(..., alias="_id")
    budget: Optional[float] = Field(default=100.0, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class User(BaseModel):
    """User model for database operations."""
    name: str
    email: EmailStr
    password: str
    budget: Optional[float] = Field(default=100.0, ge=0, description="Monthly grocery budget")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None