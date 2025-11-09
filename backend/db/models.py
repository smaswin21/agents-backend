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
    "carts": "carts"
}

# Helper functions for MongoDB operations
async def create_document(collection_name: str, data: Dict[str, Any]) -> str:
    """Create a document and return its ID."""
    from db.mongo import get_db
    db = get_db()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_name].insert_one(data)
    return str(result.inserted_id)


async def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by ID."""
    from db.mongo import get_db
    db = get_db()
    doc = await db[collection_name].find_one({"_id": ObjectId(doc_id)})
    return to_dict(doc) if doc else None


async def update_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
    """Update a document."""
    from db.mongo import get_db
    db = get_db()
    data["updated_at"] = datetime.utcnow()
    result = await db[collection_name].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": data}
    )
    return result.modified_count > 0


async def find_documents(collection_name: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find multiple documents."""
    from db.mongo import get_db
    db = get_db()
    cursor = db[collection_name].find(filter_dict)
    docs = await cursor.to_list(length=None)
    return [to_dict(doc) for doc in docs]