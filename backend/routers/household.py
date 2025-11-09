"""
Household management endpoints for creating, joining, and managing households.
"""
import random
import string
from typing import List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
import os

router = APIRouter(prefix="/household", tags=["household"])

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://aswin:agent@cluster0.gjdoeot.mongodb.net/household?retryWrites=true&w=majority&appName=Cluster0")
MONGO_DB = os.getenv("MONGO_DB", "household")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
household_collection = db.households


# Schemas
class HouseholdPreferences(BaseModel):
    name: str
    members: int
    common_items: List[str]
    pantry_amounts: dict[str, str] 
    users: List[EmailStr]


def _generate_unique_invite_code() -> str:
    """Generate a unique 5-character invite code."""
    alphabet = string.ascii_uppercase
    while True:
        code = ''.join(random.choices(alphabet, k=5))
        # ensure uniqueness in the collection
        if not household_collection.find_one({"invite_code": code}):
            return code


@router.post("/preferences")
async def save_household_preferences(data: HouseholdPreferences = Body(...)):
    """
    Creates a household and automatically adds the logged-in user's email.
    """
    payload = {
        "name": data.name,
        "members": data.members,
        "common_items": data.common_items,
        "pantry_amounts": data.pantry_amounts,
        "invite_code": _generate_unique_invite_code(),
        "users": data.users,  # uses list of emails from form
    }

    result = household_collection.insert_one(payload)

    return {
        "message": "Household created",
        "household_id": str(result.inserted_id),
        "invite_code": payload["invite_code"],
    }


@router.get("/my")
async def get_household_for_user(email: EmailStr = Query(...)):
    """
    Returns the household the user belongs to based on their email.
    If found: { in_household: true, household: {...}, dashboard_url: "/dashboard/<id>" }
    If not:   { in_household: false }
    """
    doc = household_collection.find_one({"users": str(email)}, {
        "_id": 1,
        "name": 1,
        "members": 1,
        "common_items": 1,
        "invite_code": 1,
        "users": 1,
    })

    if not doc:
        return {"in_household": False}

    hid = str(doc.get("_id"))
    household = {
        "id": hid,
        "name": doc.get("name"),
        "members": doc.get("members"),
        "common_items": doc.get("common_items", []),
        "invite_code": doc.get("invite_code"),
        "users": doc.get("users", []),
    }

    return {
        "in_household": True,
        "household": household,
    }


@router.post("/join")
async def join_household_new_user(email: EmailStr = Query(...), code: str = Query(...)):
    """
    Join a household by invite code.
    - Looks up the household by invite_code
    - Adds the user's email to the users array (no duplicates)
    """
    # 1) Find household by invite code
    doc = household_collection.find_one({"invite_code": code})
    if not doc:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # 2) If already a member, return 409 to indicate no change
    if str(email) in doc.get("users", []):
        return {
            "message": "Already a member of this household",
            "household_id": str(doc["_id"]),
            "dashboard_url": f"/dashboard/{str(doc['_id'])}"
        }

    # 3) Add user to the household users array (deduplicated)
    res = household_collection.update_one(
        {"_id": doc["_id"]},
        {"$addToSet": {"users": str(email)}}
    )

    if res.modified_count == 0 and str(email) not in doc.get("users", []):
        # Shouldn't happen, but handle race conditions
        raise HTTPException(status_code=500, detail="Failed to join household")

    hid = str(doc["_id"])
    return {
        "message": "Joined household",
        "household_id": hid,
        "dashboard_url": f"/dashboard/{hid}"
    }
