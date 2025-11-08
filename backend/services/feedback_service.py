"""Feedback Service - Business logic for item feedback operations."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from db.models import create_document, find_documents, COLLECTIONS
from schemas.pantry import ItemFeedbackCreate, ItemFeedbackResponse


async def create_feedback(item_id: str, household_id: str, feedback_data: ItemFeedbackCreate) -> str:
    """Create a new feedback entry."""
    data = feedback_data.model_dump(exclude_unset=True)
    data["item_id"] = item_id
    data["household_id"] = household_id
    feedback_id = await create_document(COLLECTIONS["item_feedback"], data)
    return feedback_id


async def get_recent_feedback(item_id: str, hours: int = 72) -> List[Dict[str, Any]]:
    """Get feedback for an item within the last N hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    docs = await find_documents(COLLECTIONS["item_feedback"], {
        "item_id": item_id,
        "created_at": {"$gte": cutoff}
    })
    return docs


async def aggregate_feedback_by_item(household_id: str, hours: int = 72) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate feedback per item for the last N hours.
    Returns: {item_id: {"fine": count, "dwindling": count, "empty": count, "distinct_users": set}}
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    docs = await find_documents(COLLECTIONS["item_feedback"], {
        "household_id": household_id,
        "created_at": {"$gte": cutoff}
    })
    
    aggregated = {}
    for doc in docs:
        item_id = doc["item_id"]
        if item_id not in aggregated:
            aggregated[item_id] = {"fine": 0, "dwindling": 0, "empty": 0, "distinct_users": set()}
        
        status = doc.get("status", "").lower()
        if status in aggregated[item_id]:
            aggregated[item_id][status] += 1
        aggregated[item_id]["distinct_users"].add(doc["user_id"])
    
    # Convert sets to counts
    for item_id in aggregated:
        aggregated[item_id]["distinct_users"] = len(aggregated[item_id]["distinct_users"])
    
    return aggregated