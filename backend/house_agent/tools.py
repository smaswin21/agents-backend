
"""
LangGraph tools for the household agent.
These tools interact with MongoDB to fetch and analyze household data.
"""
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add backend to path so we can import from it
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from db.models import find_documents, get_document, create_document, COLLECTIONS


# Collection name constants
COLLECTION_GROCERY_LISTS = COLLECTIONS["grocery_lists"]
COLLECTION_PANTRY_ITEMS = COLLECTIONS["pantry_items"]
COLLECTION_HOUSEHOLDS = COLLECTIONS["households"]
COLLECTION_USERS = COLLECTIONS["users"]
COLLECTION_carts = COLLECTIONS["carts"]


# Helper function to run async functions synchronously
def _run_async(coro):
    """Run an async coroutine and return the result."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# Simple test tool to verify tool calling works
def add_numbers(a: float, b: float) -> str:
    """
    Return the sum of a and b as a string.
    Keep output a string (ToolMessage requires string content).
    """
    result = float(a) + float(b)
    print(f"TOOL CALLED: add_numbers({a}, {b}) -> {result}")
    return str(result)


# Unified database query function
def query_household_data(
    household_id: str,
    collection_name: str,
    query_type: str = "fetch",
    additional_filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Unified function to query household data from any collection.
    
    Args:
        household_id: The household ID to query for
        collection_name: Name of the collection to query ('grocery_lists', 'pantry_items', etc.)
        query_type: Type of query - 'fetch', 'analyze', or 'budget'
        additional_filters: Additional MongoDB filters to apply
        
    Returns:
        Formatted string with query results
    """
    async def _query():
        # Build the filter
        filter_dict = {"household_id": household_id}
        if additional_filters:
            filter_dict.update(additional_filters)
        
        if query_type == "fetch":
            # Fetch items from collection
            items = await find_documents(collection_name, filter_dict)
            
            if not items:
                return f"No items found in {collection_name} for household."
            
            # Format based on collection type
            if collection_name == COLLECTION_GROCERY_LISTS:
                all_items = []
                for grocery_list in items:
                    all_items.extend(grocery_list.get("items", []))
                
                formatted = []
                for item in all_items:
                    name = item.get('item_name', 'Unknown')
                    quantity = item.get('quantity', 0)
                    brand = item.get('brand', 'Any')
                    
                    if quantity == 0:
                        status = "OUT"
                    elif quantity < 3:
                        status = "LOW"
                    else:
                        status = "OK"
                    
                    formatted.append(
                        f"- {name}: quantity={quantity}, brand={brand}, status={status}"
                    )
                return "\n".join(formatted)
            
            elif collection_name == COLLECTION_PANTRY_ITEMS:
                formatted = []
                for item in items:
                    name = item.get("item_name", "Unknown")
                    on_hand = item.get("on_hand", 0)
                    par_level = item.get("par_level", 0)
                    formatted.append(
                        f"- {name}: on_hand={on_hand}, par_level={par_level}"
                    )
                return "\n".join(formatted)
            
            elif collection_name == COLLECTION_carts:
                formatted = []
                total_price = 0
                for item in items:
                    name = item.get("item_name", "Unknown")
                    quantity = item.get("quantity", 0)
                    price = item.get("price", 0)
                    total_price += price * quantity
                    formatted.append(
                        f"- {name}: quantity={quantity}, price=${price:.2f}, total=${price * quantity:.2f}"
                    )
                formatted.append(f"\nTotal Cart Value: ${total_price:.2f}")
                return "\n".join(formatted)
            
            else:
                # Generic formatting for other collections
                return f"Found {len(items)} items in {collection_name}"
        
        elif query_type == "analyze":
            # Analyze items (specifically for pantry)
            items = await find_documents(collection_name, filter_dict)
            
            if not items:
                return f"No items to analyze in {collection_name}."
            
            low_items = []
            out_items = []
            
            for item in items:
                name = item.get("item_name", "Unknown")
                on_hand = item.get("on_hand", 0)
                par_level = item.get("par_level", 0)
                
                if on_hand == 0:
                    out_items.append(f"{name} (OUT)")
                elif on_hand < par_level:
                    low_items.append(f"{name} (LOW: {on_hand}/{par_level})")
            
            result = []
            if out_items:
                result.append(f"OUT OF STOCK: {', '.join(out_items)}")
            if low_items:
                result.append(f"RUNNING LOW: {', '.join(low_items)}")
            
            return "\n".join(result) if result else "All items are stocked."
        
        elif query_type == "budget":
            # Fetch budget information
            household = await get_document(COLLECTION_HOUSEHOLDS, household_id)
            if household and "budget_weekly" in household:
                return f"${household['budget_weekly']:.2f}"
            
            # Fallback to user budget
            user = await get_document(COLLECTION_USERS, household_id)
            if user and "budget" in user:
                return f"${user['budget']:.2f}"
            
            return "$100.00"  # Default fallback
        
        else:
            return f"Unknown query_type: {query_type}"
    
    return _run_async(_query())


def add_items_to_cart(household_id: str, items: List[Dict[str, Any]]) -> str:
    """
    Add items to the shopping cart collection.
    Creates a new shopping cart document or updates existing one.
    
    Args:
        household_id: The household ID
        items: List of items to add to cart, each with item_name, quantity, price, brand, etc.
        
    Returns:
        Success message with cart ID
    """
    async def _add():
        cart_data = {
            "household_id": household_id,
            "items": items,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        doc_id = await create_document(COLLECTION_carts, cart_data)
        return f"Successfully added {len(items)} items to shopping cart. Cart ID: {doc_id}"
    
    return _run_async(_add())


def get_carts(household_id: str) -> str:
    """
    Retrieve the active shopping cart for a household.
    
    Args:
        household_id: The household ID
        
    Returns:
        Formatted string with cart contents
    """
    return query_household_data(
        household_id=household_id,
        collection_name=COLLECTION_carts,
        query_type="fetch",
        additional_filters={"status": "active"}
    )


# Convenience functions that use the unified query function
def fetch_household_inventory(household_id: str) -> str:
    """Fetch all grocery items for a household."""
    return query_household_data(household_id, COLLECTION_GROCERY_LISTS, "fetch")


def fetch_household_budget(household_id: str) -> str:
    """Fetch the household's grocery budget."""
    return query_household_data(household_id, COLLECTION_HOUSEHOLDS, "budget")


def analyze_pantry_items(household_id: str) -> str:
    """Analyze pantry items to identify what's running low."""
    return query_household_data(household_id, COLLECTION_PANTRY_ITEMS, "analyze")

# --- compatibility tools for LangGraph ---

def add_item_sync(
    household_id: str,
    item_name: str,
    quantity: int = 1,
    price: float = 0.0,
    brand: str = "Any",
    collection: str = "carts",
) -> str:
    """
    Add a SINGLE item for this household.
    This is the name graph.py expects.
    By default we drop it in the carts collection.
    """
    item = {
        "item_name": item_name,
        "quantity": quantity,
        "price": price,
        "brand": brand,
    }

    # if you're treating shopping cart as its own collection:
    if collection == "carts":
        return add_items_to_cart(household_id, [item])

    # otherwise create a document directly in the chosen collection
    async def _add():
        data = {
            "household_id": household_id,
            **item,
        }
        doc_id = await create_document(collection, data)
        return f"Added {item_name} to {collection} with id {doc_id}"

    return _run_async(_add())


def bulk_add_items_sync(
    household_id: str,
    items: List[Dict[str, Any]],
    collection: str = "carts",
) -> str:
    """
    Add MULTIPLE items for this household.
    This is the bulk version graph.py wants.
    """
    # normalize items a bit
    normalized = []
    for it in items:
        normalized.append({
            "item_name": it.get("item_name") or it.get("name") or "Unknown item",
            "quantity": it.get("quantity", 1),
            "price": it.get("price", 0.0),
            "brand": it.get("brand", "Any"),
        })

    if collection == "carts":
        return add_items_to_cart(household_id, normalized)

    async def _add_bulk():
        # if you really want to insert into some other collection, do it one by one
        ids = []
        for it in normalized:
            data = {"household_id": household_id, **it}
            doc_id = await create_document(collection, data)
            ids.append(doc_id)
        return f"Added {len(ids)} items to {collection}: {ids}"

    return _run_async(_add_bulk())