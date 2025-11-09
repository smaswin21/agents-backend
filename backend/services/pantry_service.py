"""Pantry Service - Business logic for pantry item operations."""

from typing import List, Optional
from datetime import datetime
from db.models import create_document, get_document, update_document, find_documents, COLLECTIONS
from schemas.pantry import PantryItemCreate, PantryItemUpdate, PantryItemResponse, PantryItemBulkCreate


async def create_pantry_item(item_data: PantryItemCreate) -> str:
    """Create a new pantry item. Automatically calculates is_low status."""
    data = item_data.model_dump(exclude_unset=True)
    data["is_low"] = data["on_hand"] < data["par_level"]
    if "last_added_at" not in data:
        data["last_added_at"] = None
    item_id = await create_document(COLLECTIONS["pantry_items"], data)
    return item_id


async def bulk_create_pantry_items(bulk_data: PantryItemBulkCreate) -> List[str]:
    """Create multiple pantry items in one operation."""
    item_ids = []
    for item_data in bulk_data.items:
        item_dict = item_data.model_dump(exclude_unset=True)
        item_dict["household_id"] = bulk_data.household_id
        item_dict["is_low"] = item_dict["on_hand"] < item_dict["par_level"]
        if "last_added_at" not in item_dict:
            item_dict["last_added_at"] = None
        item_id = await create_document(COLLECTIONS["pantry_items"], item_dict)
        item_ids.append(item_id)
    return item_ids


async def get_pantry_item(item_id: str) -> Optional[PantryItemResponse]:
    """Get a pantry item by ID."""
    doc = await get_document(COLLECTIONS["pantry_items"], item_id)
    if not doc:
        return None
    return PantryItemResponse(**doc)


async def update_pantry_item(item_id: str, update_data: PantryItemUpdate) -> bool:
    """Update a pantry item. Automatically recalculates is_low status."""
    item = await get_document(COLLECTIONS["pantry_items"], item_id)
    if not item:
        return False
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if "on_hand" in update_dict or "par_level" in update_dict:
        new_on_hand = update_dict.get("on_hand", item.get("on_hand", 0))
        new_par_level = update_dict.get("par_level", item.get("par_level", 0))
        update_dict["is_low"] = new_on_hand < new_par_level
    
    return await update_document(COLLECTIONS["pantry_items"], item_id, update_dict)


async def get_all_pantry_items(household_id: str) -> List[PantryItemResponse]:
    """Get all pantry items for a household with computed status."""
    docs = await find_documents(COLLECTIONS["pantry_items"], {
        "household_id": household_id
    })
    return [PantryItemResponse(**doc) for doc in docs]


async def update_last_added_at(item_id: str) -> bool:
    """Update the last_added_at timestamp for an item."""
    return await update_document(COLLECTIONS["pantry_items"], item_id, {
        "last_added_at": datetime.utcnow()
    })