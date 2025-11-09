"""
Shopping Cart router — shared grocery cart keyed by household invite_code.
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
import os

router = APIRouter(prefix="/shopping-cart", tags=["shopping-cart"])

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://aswin:agent@cluster0.gjdoeot.mongodb.net/household?retryWrites=true&w=majority&appName=Cluster0")
MONGO_DB = os.getenv("MONGO_DB", "household")
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
shopping_cart = db.shopping_cart
households = db.households

shopping_cart.create_index("invite_code")
households.create_index("invite_code")

# Schemas
class CartItem(BaseModel):
    name: str
    quantity: int = 1

class ShoppingCartOut(BaseModel):
    invite_code: str
    items: List[CartItem] = []

class ShoppingCartPut(BaseModel):
    invite_code: str
    items: List[CartItem]

class ShoppingCartPatchAdd(BaseModel):
    invite_code: str
    item: CartItem

def _require_household(invite_code: str):
    h = households.find_one({"invite_code": invite_code}, {"_id": 1})
    if not h:
        raise HTTPException(status_code=404, detail="Household not found for invite_code")

@router.get("/", response_model=ShoppingCartOut)
async def get_cart(invite_code: Optional[str] = Query(None), email: Optional[str] = Query(None)):
    if not invite_code and not email:
        raise HTTPException(status_code=400, detail="Provide invite_code or email")

    # resolve invite_code by email if needed
    if not invite_code and email:
        h = households.find_one({"users": str(email)}, {"invite_code": 1})
        if not h or not h.get("invite_code"):
            raise HTTPException(status_code=404, detail="User not in a household (or missing invite_code)")
        invite_code = h["invite_code"]

    _require_household(invite_code)

    cart = shopping_cart.find_one({"invite_code": invite_code})
    if not cart:
        # auto-create empty cart on first access
        shopping_cart.insert_one({"invite_code": invite_code, "items": []})
        return {"invite_code": invite_code, "items": []}

    # normalize
    items = []
    for it in cart.get("items", []):
        if isinstance(it, str):
            items.append({"name": it, "quantity": 1})
        else:
            items.append({"name": it.get("name", ""), "quantity": int(it.get("quantity", 1))})

    return {"invite_code": invite_code, "items": items}

@router.put("/", response_model=ShoppingCartOut)
async def replace_cart(data: ShoppingCartPut = Body(...)):
    _require_household(data.invite_code)

    shopping_cart.update_one(
        {"invite_code": data.invite_code},
        {"$set": {"items": [i.dict() for i in data.items]}},
        upsert=True
    )
    return {"invite_code": data.invite_code, "items": data.items}

@router.patch("/add", response_model=ShoppingCartOut)
async def add_item(data: ShoppingCartPatchAdd = Body(...)):
    """
    Add or upsert a single item (by name). If the item exists, quantity is replaced.
    """
    _require_household(data.invite_code)

    shopping_cart.update_one(
        {"invite_code": data.invite_code, "items.name": data.item.name},
        {"$set": {"items.$.quantity": data.item.quantity}}
    )
    # if not found, push new
    shopping_cart.update_one(
        {"invite_code": data.invite_code, "items.name": {"$ne": data.item.name}},
        {"$push": {"items": data.item.dict()}},
        upsert=True
    )
    updated = shopping_cart.find_one({"invite_code": data.invite_code}) or {"items": []}
    return {"invite_code": data.invite_code, "items": updated.get("items", [])}
