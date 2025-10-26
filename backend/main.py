"""
FastAPI main server for JOL AI Agent
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn

from models import (
    ChatRequest, ChatResponse, ListingResponse,
    ListingCreateRequest, ActionResult, SuggestedAction
)
from database import db
from agent_v2 import agent
from config import HOST, PORT, RELOAD, CORS_ORIGINS


# === Lifespan events ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Initialize database
    print("🚀 Starting JOL AI Agent Server...")
    await db.init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("👋 Shutting down server...")


# === FastAPI App ===

app = FastAPI(
    title="JOL AI Agent",
    description="중고거래 AI 어시스턴트 챗봇",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Routes ===

@app.get("/")
async def root():
    """Serve frontend HTML"""
    return FileResponse("../frontend/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "JOL AI Agent"}


# === Chat Endpoint ===

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message and execute agent actions

    Args:
        request: ChatRequest with user message

    Returns:
        ChatResponse with agent response and actions
    """
    try:
        # Process message through agent with history
        result = await agent.process_message(request.message, history=request.history)

        # Convert to response format
        actions_taken = [
            ActionResult(
                tool=action["tool"],
                result=action["result"]
            )
            for action in result["actions_taken"]
        ]

        suggested_actions = [
            SuggestedAction(**action)
            for action in result["suggested_actions"]
        ]

        return ChatResponse(
            response=result["response"],
            reasoning=result["reasoning"],
            actions_taken=actions_taken,
            suggested_actions=suggested_actions,
            updated_listings=result["updated_listings"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# === Listings Endpoints ===

@app.get("/listings", response_model=list[ListingResponse])
async def get_listings(
    status: str = "active",
    sort_by: str = "created_at",
    sort_order: str = "DESC"
):
    """
    Get all listings with optional status filter and sorting

    Args:
        status: Listing status filter (default: "active")
        sort_by: Sort field (created_at, updated_at, last_boosted_at, price, boost_count)
        sort_order: Sort order (ASC or DESC, default: DESC)

    Returns:
        List of listings
    """
    try:
        listings = await db.get_all_listings(
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return [ListingResponse(**listing) for listing in listings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: int):
    """
    Get single listing by ID

    Args:
        listing_id: Listing ID

    Returns:
        Listing details
    """
    try:
        listing = await db.get_listing_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")
        return ListingResponse(**listing)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/listings", response_model=ListingResponse)
async def create_listing(request: ListingCreateRequest):
    """
    Create new listing

    Args:
        request: ListingCreateRequest with listing details

    Returns:
        Created listing
    """
    try:
        listing_id = await db.create_listing(
            title=request.title,
            content=request.content,
            price=request.price,
            category=request.category,
            region=request.region
        )

        # Fetch created listing
        listing = await db.get_listing_by_id(listing_id)
        return ListingResponse(**listing)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# === Static files (CSS, JS) ===

app.mount("/static", StaticFiles(directory="../frontend"), name="static")


# === Main entry point ===

if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║       JOL - 중고거래 AI 어시스턴트 챗봇                  ║
    ║                                                          ║
    ║       Server: http://{HOST}:{PORT}                     ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD
    )
