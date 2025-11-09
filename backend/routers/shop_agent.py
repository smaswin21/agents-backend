"""
Shopping agent router.
Exposes API endpoints for AI-powered shopping decisions.
"""
from fastapi import APIRouter, HTTPException
from schemas.shopping_agent import AgentDecisionRequest, AgentDecisionResponse
from agents.shopping_agent_service import decide_shopping_cart

router = APIRouter(prefix="/shopping-agent", tags=["Shopping Agent"])

@router.post("/decide", response_model=AgentDecisionResponse)
async def trigger_shopping_agent(request: AgentDecisionRequest) -> AgentDecisionResponse:
    """
    Trigger the shopping agent to analyze inventory and draft a shopping cart.
    
    Returns a 3-bullet summary:
    - Top status (critical item out/low)
    - Action summary (what to buy + reason)
    - Cart reference (cart ID for approval)
    
    Example request:
    ```json
    {
        "owner_id": "user123",
        "budget": 50.0
    }
    ```
    
    Example response:
    ```json
    {
        "top_status": "Toilet paper is out.",
        "action_summary": "Buy 2 packs — lowest price per unit",
        "cart_reference": "Cart prepared — approve list GL4F2A1C",
        "cart_id": "GL4F2A1C",
        "items": [
            {
                "item_name": "Toilet Paper",
                "quantity": 2,
                "estimated_price": 12.99,
                "reason": "Out of stock, bulk discount available"
            }
        ],
        "total_cost": 12.99
    }
    ```
    """
    try:
        decision = await decide_shopping_cart(
            owner_id=request.owner_id,
            budget_override=request.budget
        )
        return decision
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")