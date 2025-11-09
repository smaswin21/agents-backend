""" LangGraph tools for the household agent. These tools interact with MongoDB to fetch and analyze household data. """
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
    Add items to the shopping cart collection. Creates a new shopping cart document or updates existing one.

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


# ASWIN
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


from db.mongo import get_db  # uses your MongoDB helper
from db.models import COLLECTIONS

COLLECTION_GROCERY_LISTS = COLLECTIONS["grocery_lists"]


# GROCERY LIST (item_name, quantity)
# def bump_quantity_by_two(household_id: str, item_name: str, NUMBER) -> str:
#     """
#     Increment the quantity of a specific item in grocery_lists by {NUMBER}.
#     Matches with the given {item_name} and increases its quantity by {NUMBER}.
#     """
#     async def _update():
#         db = get_db()
#         coll = db[COLLECTION_GROCERY_LISTS]
#         result = await coll.update_one(
#             {"household_id": household_id, "items.item_name": item_name},
#             {"$inc": {"items.$.quantity": {NUMBER}}}
#         )
#         if result.matched_count == 0:
#             return f"Item '{item_name}' not found for household '{household_id}'."
#         return f"Increased '{item_name}' quantity by {NUMBER}."
#
#     print("TOOL CALLED: bump_quantity_by_two")
#     return _run_async(_update())


# GROCERY LIST (item_name, quantity)
def bump_item_quantity(household_id: str, item_name: str, quantity: int) -> str:
    """
    Increment the quantity of a specific item in grocery_lists by {quantity}.
    Finds the grocery list entry with the given {item_name} for a specific {household_id}
    and increases its quantity by {quantity}.
    """

    async def _update():
        db = get_db()
        coll = db[COLLECTION_GROCERY_LISTS]

        # increment the item's quantity
        result = await coll.update_one(
            {"household_id": household_id, "items.item_name": item_name},
            {"$inc": {"items.$.quantity": quantity}}
        )

        # handle if item not found
        if result.matched_count == 0:
            return f"Item '{item_name}' not found for household '{household_id}'."
        return f"Increased '{item_name}' quantity by {quantity}."

    print("TOOL CALLED: bump_item_quantity")
    return _run_async(_update())
