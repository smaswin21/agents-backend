"""
Main FastAPI application entry point.
Includes all routers and middleware configuration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import routers
from routers.root import router as root_router
from routers.health import router as health_router
from routers.auth import router as auth_router
from routers.household import router as household_router
from routers.agent_messages import router as agent_messages_router
from routers.house_agent import router as house_agent_router
from routers.shopping_cart import router as shopping_cart_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Agents Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(root_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(household_router)
app.include_router(agent_messages_router)
app.include_router(house_agent_router)
app.include_router(shopping_cart_router)
