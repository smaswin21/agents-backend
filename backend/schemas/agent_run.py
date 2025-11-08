"""
Agent run tracking schema.
For traceability and debugging agent executions.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents in the system."""
    PANTRY = "pantry"
    GROCERY = "grocery"


class RunStatus(str, Enum):
    """Status of an agent run."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunBase(BaseModel):
    """Base agent run fields."""
    agent_type: AgentType
    household_id: str
    trigger: str = Field(..., description="What triggered this run (event/schedule)")


class AgentRunCreate(AgentRunBase):
    """Schema for creating an agent run record."""
    pass


class AgentRunResponse(AgentRunBase):
    """Schema for agent run responses."""
    id: str = Field(..., alias="_id")
    status: RunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions_taken: List[str] = Field(default_factory=list, description="What the agent did")
    errors: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True