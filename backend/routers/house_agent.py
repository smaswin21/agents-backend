"""
FastAPI router for house_agent endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from langchain_core.messages import HumanMessage

from house_agent.graph import build_graph

# Router setup

router = APIRouter(prefix="/house-agent", tags=["house-agent"])

# Build the agent graph once at module level
agent_graph = build_graph()


# Request & Response Schemas

class ChatRequest(BaseModel):
    """Request schema for the chat endpoint."""
    message: str = Field(..., description="User message to send to the agent")
    household_id: Optional[str] = Field(None, description="Associated household ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_id: Optional[str] = Field(None, description="Session/conversation ID")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    """Response schema for the chat endpoint."""
    response: str = Field(..., description="Agent's response message")
    session_id: Optional[str] = Field(None, description="Session/conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata (tool calls, etc.)"
    )

# Routes

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the household agent.

    Sends a message to the agent and returns the response.
    The agent can use tools to fetch inventory, budget, and manage household data.
    """
    try:
        # Initialize conversation state
        state = {"messages": []}

        # TODO: Convert prior conversation_history to LangChain message types if needed
        # For now, just append the new user message
        state["messages"].append(HumanMessage(content=request.message))

        # Run the agent graph
        result_state = agent_graph.invoke(state)

        # Extract the agent's last message
        last_msg = result_state["messages"][-1]
        agent_response = getattr(last_msg, "content", str(last_msg))

        # Collect metadata (e.g., tool calls)
        metadata = {}
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            metadata["tool_calls"] = [
                {"name": tc.get("name"), "id": tc.get("id")}
                for tc in last_msg.tool_calls
            ]

        return ChatResponse(
            response=agent_response,
            session_id=request.session_id,
            metadata=metadata
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


@router.get("/health")
async def health():
    """Health check endpoint for house agent."""
    return {"status": "ok", "service": "house-agent"}

