"""
Agent messages endpoints for long-polling agent responses.
"""
from typing import Optional
import asyncio
from fastapi import APIRouter, Query, Response
from pydantic import BaseModel
from pymongo import MongoClient
import os

router = APIRouter(prefix="/agent/messages", tags=["agent-messages"])

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://aswin:agent@cluster0.gjdoeot.mongodb.net/household?retryWrites=true&w=majority&appName=Cluster0")
MONGO_DB = os.getenv("MONGO_DB", "household")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
agent_messages_collection = db.agent_messages


# Schemas
class AgentMessageOut(BaseModel):
    message: str
    created_at: str


@router.get(
    "/long-poll",
    response_model=AgentMessageOut,
    responses={204: {"description": "No new message within timeout"}}
)
async def long_poll_agent_message(
    since: Optional[str] = Query(None, description="Last seen created_at (ISO8601, e.g. 2025-11-09T02:45:10Z)"),
    poll_interval_ms: int = Query(500, ge=100, le=5000, description="DB check interval in ms")
):
    """
    Long-poll the latest agent message. Returns immediately if a newer message exists.
    If nothing new arrives within `timeout` seconds -> 204 No Content.
    """
    loop = asyncio.get_event_loop()
    timeout = 25
    deadline = loop.time() + timeout

    while True:
        doc = agent_messages_collection.find_one(sort=[("created_at", -1)])
        if doc:
            created_at = doc.get("created_at")
            # Return if client has no 'since' or the latest differs
            if not since or (created_at and created_at != since):
                return {"message": doc.get("message", ""), "created_at": created_at}

        # timeout reached -> no new content
        if loop.time() >= deadline:
            return Response(status_code=204)

        # sleep briefly before checking again
        await asyncio.sleep(poll_interval_ms / 1000)
