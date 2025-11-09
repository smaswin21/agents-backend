"""
MongoDB collection models and helpers.
These define the structure of documents stored in MongoDB.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId

def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to dict with string ID."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# Collection names
COLLECTIONS = {
    "households": "households",
    "users": "users",
    "pantry_items": "pantry_items",
    "grocery_lists": "grocery_lists",
    "item_feedback": "item_feedback" ,
    "carts": "carts",
    "agent_messages": "agent_messages"
}

# Helper functions for MongoDB operations
async def create_document(collection_name: str, data: Dict[str, Any]) -> str:
    """Create a document and return its ID."""
    from backend.db.mongo import get_db
    db = get_db()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_name].insert_one(data)
    return str(result.inserted_id)


async def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by ID."""
    from backend.db.mongo import get_db
    db = get_db()
    doc = await db[collection_name].find_one({"_id": ObjectId(doc_id)})
    return to_dict(doc) if doc else None


async def update_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
    """Update a document."""
    from backend.db.mongo import get_db
    db = get_db()
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_name].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": data}
    )
    return result.modified_count > 0


async def find_documents(collection_name: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find multiple documents."""
    from backend.db.mongo import get_db
    db = get_db()
    cursor = db[collection_name].find(filter_dict)
    docs = await cursor.to_list(length=None)
    return [to_dict(doc) for doc in docs]


async def store_agent_message(
    message: str,
    household_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Store an agent response message in the agent_messages collection.

    Args:
        message: The agent's response text
        household_id: Optional household ID to associate with the message
        user_id: Optional user ID to associate with the message
        session_id: Optional session/conversation ID for grouping messages
        metadata: Optional metadata (tool calls, execution time, etc.)

    Returns:
        The inserted document ID as a string
    """
    data = {
        "message": message,
        "household_id": household_id,
        "user_id": user_id,
        "session_id": session_id,
        "metadata": metadata or {}
    }
    return await create_document(COLLECTIONS["agent_messages"], data)