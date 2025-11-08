from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

""" 
fetch_existing_items(): Gets inventory from grocery_items collection
fetch_budget(): Retrieves user's budget from users collection
decide_shopping_cart(): Main orchestrator that runs the LangChain agent
generate_cart_id(): Creates unique cart IDs (e.g., "GL4F2A1C")
"""

class CartItem(BaseModel):
    """Single item in a shopping cart."""
    item_name: str
    quantity: int
    estimated_price: Optional[float] = None
    reason: Optional[str] = None


class ShoppingCart(BaseModel):
    """A drafted shopping cart stored in the database."""
    cart_id: str
    items: List[CartItem]
    total_estimated_cost: float
    created_at: datetime
    status: str = "pending"  # pending, approved, rejected
    owner_id: str


class AgentDecisionRequest(BaseModel):
    """Request to trigger the shopping agent."""
    owner_id: str
    budget: Optional[float] = None  # Override budget if provided


class AgentDecisionResponse(BaseModel):
    """3-bullet summary response from the agent."""
    top_status: str = Field(..., description="Top status line (e.g., 'Toilet paper is out.')")
    action_summary: str = Field(..., description="Action + quantity + one-line reason")
    cart_reference: str = Field(..., description="Cart prepared message with ID (e.g., 'Cart prepared — approve list GL123')")
    cart_id: str = Field(..., description="The cart ID for the frontend to reference")
    items: List[CartItem] = Field(..., description="Full list of items in the cart")
    total_cost: float