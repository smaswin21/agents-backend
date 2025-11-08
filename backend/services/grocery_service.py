"""Grocery Service - Business logic for grocery list operations."""
from typing import List, Optional
from datetime import datetime
from db.models import create_document, get_document, update_document, find_documents, COLLECTIONS
from schemas.grocery_list import (
    GroceryListCreate, GroceryListUpdate, GroceryListResponse, 
    ListStatus, ListItem, GroceryListApproveResponse
)


async def create_grocery_list(list_data: GroceryListCreate) -> str:
    """Create a new grocery list. Sets initial status to DRAFT."""
    data = list_data.model_dump(exclude_unset=True)
    data["status"] = ListStatus.DRAFT.value
    if "items" not in data:
        data["items"] = []
    if "agent_notes" not in data:
        data["agent_notes"] = None
    if "cost_estimate" not in data:
        data["cost_estimate"] = None
    if "eta" not in data:
        data["eta"] = None
    list_id = await create_document(COLLECTIONS["grocery_lists"], data)
    return list_id


async def get_grocery_list(list_id: str) -> Optional[GroceryListResponse]:
    """Get a grocery list by ID."""
    doc = await get_document(COLLECTIONS["grocery_lists"], list_id)
    if not doc:
        return None
    if "items" not in doc:
        doc["items"] = []
    if "agent_notes" not in doc:
        doc["agent_notes"] = None
    if "cost_estimate" not in doc:
        doc["cost_estimate"] = None
    if "eta" not in doc:
        doc["eta"] = None
    return GroceryListResponse(**doc)


async def get_current_weekly_list(household_id: str) -> Optional[GroceryListResponse]:
    """Get the current week's grocery list (draft or awaiting_approval)."""
    docs = await find_documents(COLLECTIONS["grocery_lists"], {
        "household_id": household_id,
        "status": {"$in": [ListStatus.DRAFT.value, ListStatus.AWAITING_APPROVAL.value]}
    })
    
    if docs:
        docs.sort(key=lambda x: x.get("week_start", datetime.min), reverse=True)
        doc = docs[0]
        if "items" not in doc:
            doc["items"] = []
        if "agent_notes" not in doc:
            doc["agent_notes"] = None
        if "cost_estimate" not in doc:
            doc["cost_estimate"] = None
        if "eta" not in doc:
            doc["eta"] = None
        return GroceryListResponse(**doc)
    
    return None


async def update_grocery_list(list_id: str, update_data: GroceryListUpdate) -> bool:
    """Update a grocery list."""
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if "status" in update_dict:
        if hasattr(update_dict["status"], "value"):
            update_dict["status"] = update_dict["status"].value
    
    if update_dict.get("status") == ListStatus.APPROVED.value:
        update_dict["approved_at"] = datetime.utcnow()
    
    return await update_document(COLLECTIONS["grocery_lists"], list_id, update_dict)


async def add_item_to_list(list_id: str, item: ListItem) -> bool:
    """Add an item to an existing grocery list. Deduplicates by name."""
    list_doc = await get_document(COLLECTIONS["grocery_lists"], list_id)
    if not list_doc:
        return False
    
    items = list_doc.get("items", [])
    item_dict = item.model_dump()
    
    existing_item = None
    for i in items:
        if i.get("item_name", "").lower() == item.item_name.lower():
            existing_item = i
            break
    
    if existing_item:
        existing_item["quantity"] = existing_item.get("quantity", 0) + item.quantity
        # Update reason if provided
        if item.reason:
            existing_item["reason"] = item.reason
    else:
        items.append(item_dict)
    
    return await update_document(COLLECTIONS["grocery_lists"], list_id, {"items": items})


async def approve_grocery_list(list_id: str, approved_by: str) -> GroceryListApproveResponse:
    """Approve a grocery list and return confirmation."""
    list_doc = await get_grocery_list(list_id)
    if not list_doc:
        raise ValueError(f"Grocery list {list_id} not found")
    
    update_data = GroceryListUpdate(
        status=ListStatus.APPROVED
    )
    success = await update_grocery_list(list_id, update_data)
    
    if success:
        await update_document(COLLECTIONS["grocery_lists"], list_id, {
            "approved_by": approved_by,
            "status": ListStatus.COMPLETED.value  # Mark as completed for demo
        })
    
    return GroceryListApproveResponse(
        status="approved",
        eta=list_doc.eta or "tomorrow",
        total=list_doc.cost_estimate,
        message=f"Order placed — List approved. ETA: {list_doc.eta or 'tomorrow'}"
    )