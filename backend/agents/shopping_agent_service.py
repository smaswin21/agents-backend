"""
Shopping agent service using LangChain.
Analyzes inventory and budget to make intelligent shopping decisions.
"""
from typing import Optional, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
import json

from db.models import find_documents, create_document, get_document
from schemas.shopping_agent import CartItem, ShoppingCart, AgentDecisionResponse
from utils.llm_client import get_llm_client
import os


class AgentRawOutput(BaseModel):
    """Structured output from the LLM agent."""
    top_status: str = Field(description="One-line critical status (e.g., 'Toilet paper is out.')")
    action_summary: str = Field(description="Action + quantity + reason in one line")
    items: List[CartItem] = Field(description="List of items to purchase")


async def fetch_existing_items(owner_id: str) -> List[dict]:
    """
    Fetch all grocery lists for the owner from the database.
    Uses the grocery_lists collection to get current inventory.
    """
    # Fetch all grocery lists for this owner/household
    lists = await find_documents("grocery_lists", {"household_id": owner_id})
    
    # Flatten all items from all lists into a single inventory view
    all_items = []
    for grocery_list in lists:
        items = grocery_list.get("items", [])
        all_items.extend(items)
    
    return all_items


async def fetch_budget(owner_id: str) -> Optional[float]:
    """
    Fetch the owner's budget from the user profile.
    Returns None if user not found or budget not set.
    """
    user = await get_document("users", {"_id": owner_id})
    if user:
        return user.get("budget")
    return None


async def generate_cart_id() -> str:
    """Generate a unique cart ID (e.g., GL4F2A1C)."""
    return f"GL{uuid.uuid4().hex[:6].upper()}"


async def call_llm_for_shopping_decision(items_context: str, budget: float) -> AgentRawOutput:
    """
    Call LLM via LiteLLM proxy to make shopping decisions.
    
    Args:
        items_context: Formatted inventory context
        budget: Available budget
        
    Returns:
        AgentRawOutput with structured decision
    """
    client = get_llm_client()
    if not client:
        raise ValueError("LLM client not configured. Set OPENAI_API_KEY in .env file.")
    
    model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    
    # System prompt that enforces 3-bullet format
    system_prompt = """You are a helpful shopping assistant that analyzes inventory and budget to decide what to buy.

Your response MUST be a valid JSON object with this exact structure:
{
  "top_status": "One critical line about what's out or low (e.g., 'Toilet paper is out.')",
  "action_summary": "Action + quantity + reason in one line (e.g., 'Buy 2 packs — lowest price per unit')",
  "items": [
    {
      "item_name": "string",
      "quantity": number,
      "estimated_price": number,
      "reason": "string (≤140 chars)"
    }
  ]
}

Analyze the inventory and suggest items to buy within the budget.
Prioritize items that are OUT (quantity=0) first, then LOW (quantity<3).
Keep the total cost under the budget.
Be concise and specific.
Use realistic price estimates based on typical grocery costs.
Return ONLY valid JSON, no markdown formatting."""

    user_prompt = f"""Current Inventory:
{items_context}

Budget: ${budget}

Based on this inventory, decide what items to purchase. Focus on items that are OUT or LOW.
Provide your decision as a JSON object."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=1
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        decision_data = json.loads(content)
        
        # Convert to Pydantic model
        return AgentRawOutput(**decision_data)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {str(e)}")
    except Exception as e:
        raise ValueError(f"Agent failed to generate decision: {str(e)}")


async def decide_shopping_cart(owner_id: str, budget_override: Optional[float] = None) -> AgentDecisionResponse:
    """
    LangChain-based agent that:
    1. Reads existing items and budget from DB
    2. Decides what to buy based on inventory analysis
    3. Drafts a cart with estimated costs
    4. Returns a 3-bullet summary for approval
    
    Args:
        owner_id: User/household ID
        budget_override: Optional budget override (uses user's budget if not provided)
    
    Returns:
        AgentDecisionResponse with 3-bullet summary and cart details
    """
    
    # Fetch data from database
    existing_items = await fetch_existing_items(owner_id)
    budget = budget_override if budget_override is not None else await fetch_budget(owner_id)
    
    if not budget:
        budget = 100.0  # Default fallback budget
    
    # Build context from existing items (matches your GroceryList schema)
    items_context = "\n".join([
        f"- {item.get('item_name', 'Unknown')}: quantity={item.get('quantity', 0)}, "
        f"brand={item.get('brand', 'Any')}, "
        f"shared={item.get('is_shared', True)}, "
        f"status={'OUT' if item.get('quantity', 0) == 0 else 'LOW' if item.get('quantity', 0) < 3 else 'OK'}"
        for item in existing_items
    ])
    
    if not items_context:
        items_context = "No items in inventory. Start with essential household items."
    
    # Call LLM via LiteLLM proxy
    raw_output = await call_llm_for_shopping_decision(items_context, budget)
    
    # Calculate total cost
    total_cost = sum(item.estimated_price or 0 for item in raw_output.items)
    
    # Generate cart ID
    cart_id = await generate_cart_id()
    
    # Store the cart in the database
    cart_data = ShoppingCart(
        cart_id=cart_id,
        items=raw_output.items,
        total_estimated_cost=total_cost,
        created_at=datetime.utcnow(),
        status="pending",
        owner_id=owner_id
    )
    
    await create_document("carts", cart_data.model_dump(exclude_unset=True))
    
    # Build the 3-bullet response
    cart_reference = f"Cart prepared — approve list {cart_id}"
    
    return AgentDecisionResponse(
        top_status=raw_output.top_status,
        action_summary=raw_output.action_summary,
        cart_reference=cart_reference,
        cart_id=cart_id,
        items=raw_output.items,
        total_cost=total_cost
    )