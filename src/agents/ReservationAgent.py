import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, AIMessage, ToolCall
from dotenv import load_dotenv
from langgraph.graph import MessagesState
import sys
import json
import re
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.database_operations import check_availability, reserve_room
from langchain_core.messages import AIMessage, ToolCall

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

reservation_agent_system_prompt = """
You are an AI hotel reservation assistant designed to help guests find and book available rooms.
Your tasks include:
1. Helping users find available rooms based on their requirements (date, time, capacity, features)
2. Assisting users in making room reservations once they've selected a room
3. Providing clear information about room amenities and features
4. Being courteous and professional in all interactions
5. Understanding natural language queries and translating them to proper search parameters

You have access to the following tools:

1. check_availability tool: Find available rooms matching specific criteria
   Parameters:
   - date: format YYYY-MM-DD
   - start_time: format HH:MM
   - end_time: format HH:MM
   - capacity: minimum number of people (optional)
   - features: list of required amenities like WiFi, TV, etc. (optional)

2. reserve_room tool: Make a reservation for a specific room
   Parameters:
   - room_id: the ID of the room to reserve
   - guest_name: name of the guest making the reservation
   - date: format YYYY-MM-DD
   - start_time: format HH:MM
   - end_time: format HH:MM

Workflow:
1. When a user asks about availability, confirm their requirements and use check_availability
2. Show the user the available rooms that match their criteria
3. If the user wants to book a room, collect their name and room preference, then use reserve_room
4. Confirm the reservation details with the user after booking

Always confirm the details with the user before making a reservation. If you're unsure about any details, ask for clarification.

When calling the tools, use the exact format:
check_availability(date='YYYY-MM-DD', start_time='HH:MM', end_time='HH:MM', capacity=N, features=['feature1', 'feature2'])
reserve_room(room_id=N, guest_name='Guest Name', date='YYYY-MM-DD', start_time='HH:MM', end_time='HH:MM')
"""

# Initialize chat history
reservation_agent_system_message = SystemMessage(content=reservation_agent_system_prompt)

tools = [check_availability, reserve_room]

llm = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash",
    api_key = GEMINI_API_KEY,
)

llm.bind_tools(tools)

def parse_tool_call(tool_code):
    """Parse a tool call string into a name and arguments."""
    # Extract the function name
    match = re.search(r'(\w+)\(', tool_code)
    if not match:
        return None, {}
    
    tool_name = match.group(1)
    
    # Extract the arguments
    args_text = tool_code.replace(f"{tool_name}(", "").rstrip(")")
    args_pairs = re.findall(r'(\w+)=([^,]+)(?:,|$)', args_text)
    
    args_dict = {}
    for key, value in args_pairs:
        key = key.strip()
        value = value.strip()
        
        # Handle different value types
        if value.startswith("'") or value.startswith('"'):
            # String value
            value = value[1:-1] if value.endswith(value[0]) else value
        elif value.isdigit():
            # Integer value
            value = int(value)
        elif value.startswith("[") and value.endswith("]"):
            # List value - parse items
            items_text = value[1:-1]
            items = []
            # Handle quoted strings in list
            for item in re.findall(r"'([^']*)'|\"([^\"]*)\"", items_text):
                # Each match is a tuple of two groups, one will be empty
                items.append(item[0] if item[0] else item[1])
            value = items
        
        args_dict[key] = value
    
    return tool_name, args_dict

def extract_tool_code(content):
    """Extract tool code from LLM response."""
    if "```tool_code" in content:
        return content.split("```tool_code")[1].split("```")[0].strip()
    return None

def handle_reserve_room_print_case(tool_code):
    """Handle the special case where reserve_room is inside a print statement."""
    # Extract the dictionary from the print statement
    dict_match = re.search(r'{(.*?)}', tool_code)
    if not dict_match:
        return None
        
    dict_str = '{' + dict_match.group(1) + '}'
    # Clean up the string for proper JSON parsing
    dict_str = dict_str.replace("'", '"')
    
    try:
        # Try to parse as JSON
        args_dict = json.loads(dict_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, try regex approach
        args_dict = {}
        room_id = re.search(r'"room_id":\s*(\d+)', dict_str)
        guest_name = re.search(r'"guest_name":\s*"([^"]+)"', dict_str)
        date = re.search(r'"date":\s*"([^"]+)"', dict_str)
        start_time = re.search(r'"start_time":\s*"([^"]+)"', dict_str)
        end_time = re.search(r'"end_time":\s*"([^"]+)"', dict_str)
        
        if room_id: args_dict['room_id'] = int(room_id.group(1))
        if guest_name: args_dict['guest_name'] = guest_name.group(1)
        if date: args_dict['date'] = date.group(1)
        if start_time: args_dict['start_time'] = start_time.group(1)
        if end_time: args_dict['end_time'] = end_time.group(1)
        
        # Check if we have all required parameters
        if len(args_dict) < 5:
            return None
    
    return create_reserve_room_message(args_dict)

def create_check_availability_message(args_dict):
    """Create an AIMessage with a proper tool call for check_availability."""
    tool_call = ToolCall(
        name="check_availability",
        args={"query_parameters": args_dict},
        id=f"tool_call_{hash(str(args_dict))}"
    )
    
    return AIMessage(
        content="I'll check the availability for you.",
        tool_calls=[tool_call]
    )

def create_reserve_room_message(args_dict):
    """Create an AIMessage with a proper tool call for reserve_room."""
    tool_call = ToolCall(
        name="reserve_room",
        args={"reservation_data": args_dict},
        id=f"tool_call_{hash(str(args_dict))}"
    )
    
    return AIMessage(
        content=f"I'll reserve room {args_dict.get('room_id')} for {args_dict.get('guest_name')}.",
        tool_calls=[tool_call]
    )

def process_tool_call(content):
    """Process the LLM response to extract and handle tool calls."""
    tool_code = extract_tool_code(content)
    if not tool_code:
        return None
    
    # Handle special case where model uses print or default_api
    if "print(" in tool_code or "default_api" in tool_code:
        if "reserve_room" in tool_code:
            return handle_reserve_room_print_case(tool_code)
        return None
    
    # Standard tool call parsing
    tool_name, args_dict = parse_tool_call(tool_code)
    
    if tool_name == "check_availability":
        return create_check_availability_message(args_dict)
    elif tool_name == "reserve_room":
        return create_reserve_room_message(args_dict)
    
    return None

def reservation_assistant_agent(state: MessagesState):
    """Agent function that handles reservation requests and tool calls."""
    # Combine system message and user messages into one list
    all_messages = [reservation_agent_system_message] + state['messages']
    
    # Call invoke with the correct parameter structure
    response = llm.invoke(all_messages)
    
    # Process the response for tool calls
    tool_response = process_tool_call(response.content)
    
    # If we successfully parsed a tool call, use it; otherwise use the original response
    final_response = tool_response if tool_response else response
    
    return {'messages': state['messages'] + [final_response]}