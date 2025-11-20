"""
Database Schemas for AI Booking Assistant

Each Pydantic model represents a MongoDB collection (lowercased class name).
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Booking(BaseModel):
    name: str = Field(..., description="Customer full name")
    service: str = Field(..., description="Service requested")
    date: str = Field(..., description="Preferred date (YYYY-MM-DD)")
    time: str = Field(..., description="Preferred time (HH:MM)")
    location: str = Field(..., description="Service location / address")
    phone: str = Field(..., description="Customer WhatsApp phone number with country code")
    language: str = Field("en", description="Language code (en, ne, hi, ar, es)")
    status: str = Field("pending", description="Booking status: pending/confirmed/cancelled")

class Interaction(BaseModel):
    session_id: str = Field(..., description="Conversation session id")
    role: str = Field(..., description="user or assistant")
    message: str = Field(..., description="Message content")
    language: str = Field("en", description="Language code")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Extra metadata")

class Session(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    language: str = Field("en", description="Language code")
    step: str = Field("greeting", description="Current step in booking flow")
    draft: Dict[str, Any] = Field(default_factory=dict, description="Draft booking fields collected so far")

# Example retained for reference of viewer tools
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
