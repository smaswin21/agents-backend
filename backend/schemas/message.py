"""
Agent message schema definitions.
Stores agent responses and conversation history.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentMessageCreate(BaseModel):
    """Schema for creating a new agent message."""
    message: str = Field(..., description="Agent response message content")
    household_id: Optional[str] = Field(None, description="Associated household ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_id: Optional[str] = Field(None, description="Session/conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata (tool calls, tokens, etc.)")


class AgentMessageResponse(BaseModel):
    """Schema for agent message responses."""
    id: str = Field(..., alias="_id", description="MongoDB document ID")
    message: str = Field(..., description="Agent response message content")
    household_id: Optional[str] = Field(None, description="Associated household ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_id: Optional[str] = Field(None, description="Session/conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True