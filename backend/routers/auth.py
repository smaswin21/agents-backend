"""
Authentication endpoints for user signup and login.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://aswin:agent@cluster0.gjdoeot.mongodb.net/household?retryWrites=true&w=majority&appName=Cluster0")
MONGO_DB = os.getenv("MONGO_DB", "household")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
users_collection = db.users


# Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


@router.post("/signup")
async def signup_user(user: UserCreate):
    """
    Create a new user account.
    Checks if email already exists before creating.
    """
    # Check if user already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user document
    user_data = user.model_dump()
    result = users_collection.insert_one(user_data)
    
    return {
        "message": "User created successfully",
        "user_id": str(result.inserted_id)
    }


@router.get("/login")
async def login_user(email: str = Query(...), password: str = Query(...)):
    """
    Checks if a user exists in the database with the given email and password.
    Returns success if they match, otherwise an error.
    """
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "message": "Login successful",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
    }
