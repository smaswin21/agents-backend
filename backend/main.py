from typing import Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from db.mongo import get_db
from routers.shop_agent import router as shopping_agent_router

load_dotenv()

app = FastAPI(title="Agents Backend")

# Include the routers
app.include_router(shopping_agent_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/health/db", response_class=JSONResponse)
async def health_db() -> dict[str, bool]:
    """Return {"ok": True} if a ping command to MongoDB succeeds."""
    info = await get_db().command("ping")
    return {"ok": bool(info.get("ok"))}