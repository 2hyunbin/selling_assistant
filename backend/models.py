"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# === Request Models ===

class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, description="User message")
    history: List[Dict[str, str]] = Field(default=[], description="Chat history for context")


class ListingCreateRequest(BaseModel):
    """Create new listing request"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    price: int = Field(..., gt=0, description="Price in KRW")
    category: str
    region: str


# === Response Models ===

class ListingResponse(BaseModel):
    """Listing information"""
    id: int
    title: str
    content: str
    price: int
    category: str
    region: str
    image_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    last_boosted_at: Optional[str] = None
    boost_count: int

    class Config:
        from_attributes = True


class ActionResult(BaseModel):
    """Tool execution result"""
    tool: str
    result: Dict[str, Any]


class SuggestedAction(BaseModel):
    """Suggested action button"""
    label: str
    action: str
    params: Dict[str, Any]


class ChatResponse(BaseModel):
    """Chat response with action results"""
    response: str
    reasoning: str
    actions_taken: List[ActionResult]
    suggested_actions: List[SuggestedAction]
    updated_listings: List[int]


# === Internal Models ===

class Listing(BaseModel):
    """Internal listing model"""
    id: Optional[int] = None
    title: str
    content: str
    price: int
    category: str
    region: str
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_boosted_at: Optional[datetime] = None
    boost_count: int = 0


class AgentResponse(BaseModel):
    """LLM Agent response structure"""
    intent: str
    slots: Dict[str, Any]
    tools: List[Dict[str, Any]]
    response_text: str
    reasoning: str
    suggested_actions: List[SuggestedAction]
