# src/api/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class ChatRequest(BaseModel):
    """Model for chat request payloads."""
    thread_id: str = Field(..., description="Unique identifier for the conversation thread")
    message: str = Field(..., description="The user's message to the reservation assistant")

class MessageContent(BaseModel):
    """Model for message content in responses."""
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    """Model for chat response payloads."""
    thread_id: str
    response: str
    messages: Optional[List[MessageContent]] = None

class AvailabilityQueryParams(BaseModel):
    """Parameters for room availability search."""
    date: str = Field(..., example="2023-05-15")
    start_time: str = Field(..., example="14:00")
    end_time: str = Field(..., example="16:00")
    capacity: Optional[int] = Field(1, example=2)
    features: Optional[List[str]] = Field(None, example=["WiFi", "Projector"])

class RoomReservationRequest(BaseModel):
    """Parameters for room reservation."""
    room_id: int = Field(..., example=1)
    guest_name: str = Field(..., example="John Doe")
    date: str = Field(..., example="2023-05-15")
    start_time: str = Field(..., example="14:00")
    end_time: str = Field(..., example="16:00")

class Thread(BaseModel):
    """Model for conversation thread information."""
    thread_id: str
    message_count: int