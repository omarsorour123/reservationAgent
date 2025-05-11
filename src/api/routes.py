# src/api/routes.py
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict
from api.models import (
    ChatRequest, ChatResponse, MessageContent, 
    AvailabilityQueryParams, RoomReservationRequest, Thread
)
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_operations import check_availability, reserve_room

from service.reservation_service import reservation_service
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    try:
        result = reservation_service.process_message(
            thread_id=request.thread_id, 
            user_message=request.message
        )
        
        # Format messages for the response
        formatted_messages = []
        for msg in result["messages"]:
            # Determine the role based on message type
            if hasattr(msg, 'type'):
                role = "user" if msg.type == "human" else "assistant"
            else:
                role = "system"
            
            # Extract content
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            # Extract tool calls if present
            tool_calls = None
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls = []
                for tc in msg.tool_calls:
                    # Handle both object-style and dict-style tool calls
                    if isinstance(tc, dict):
                        # If tool call is already a dictionary
                        tool_calls.append(tc)
                    else:
                        # If tool call is an object with attributes
                        tool_call_dict = {
                            "name": tc.name if hasattr(tc, 'name') else str(tc),
                            "args": tc.args if hasattr(tc, 'args') else {},
                            "id": tc.id if hasattr(tc, 'id') else ""
                        }
                        tool_calls.append(tool_call_dict)
            
            formatted_messages.append(
                MessageContent(
                    role=role,
                    content=content,
                    tool_calls=tool_calls
                )
            )
        
        return ChatResponse(
            thread_id=result["thread_id"],
            response=result["response"],
            messages=formatted_messages
        )
    except Exception as e:
        # Add error logging
        import traceback
        print(f"Error processing chat: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/threads", response_model=List[Thread])
async def list_threads():
    """List all active conversation threads."""
    threads = reservation_service.list_threads()
    return [
        Thread(
            thread_id=thread_id,
            message_count=len(reservation_service.get_conversation(thread_id))
        )
        for thread_id in threads
    ]

@router.get("/threads/{thread_id}", response_model=List[MessageContent])
async def get_thread(thread_id: str):
    """Get the conversation history for a specific thread."""
    messages = reservation_service.get_conversation(thread_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Format messages
    formatted_messages = []
    for msg in messages:
        if hasattr(msg, 'type'):
            role = "user" if msg.type == "human" else "assistant"
        else:
            role = "system"
        
        content = msg.content if hasattr(msg, 'content') else str(msg)
        
        # Extract tool calls if present
# Extract tool calls if present
        tool_calls = None
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_calls = []
            for tc in msg.tool_calls:
                # Handle both object-style and dict-style tool calls
                if isinstance(tc, dict):
                    # Tool call is already a dictionary
                    tool_calls.append(tc)
                else:
                    # Tool call is an object with attributes
                    tool_calls.append({
                        "name": tc.name if hasattr(tc, 'name') else str(tc),
                        "args": tc.args if hasattr(tc, 'args') else {},
                        "id": tc.id if hasattr(tc, 'id') else ""
                    })
        formatted_messages.append(
            MessageContent(
                role=role,
                content=content,
                tool_calls=tool_calls
            )
        )
    
    return formatted_messages

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a conversation thread."""
    if reservation_service.delete_thread(thread_id):
        return {"message": f"Thread {thread_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Thread not found")

# Direct API endpoints for room operations
@router.post("/rooms/availability", response_model=List[Dict])
async def check_room_availability(query: AvailabilityQueryParams):
    """Check for available rooms based on criteria."""
    available_rooms = check_availability(query.dict(exclude_none=True))
    return available_rooms

@router.post("/rooms/reserve", response_model=Dict)
async def reserve_room_api(reservation: RoomReservationRequest):
    """Reserve a room directly through the API."""
    reservation_result = reserve_room(reservation.dict())
    if reservation_result.get("status") == "error":
        raise HTTPException(status_code=400, detail=reservation_result.get("message"))
    return reservation_result