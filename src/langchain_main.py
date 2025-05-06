from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from database.database_operations import check_availability, reserve_room
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import json
import re
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

tools = [check_availability]
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash",
    api_key = GEMINI_API_KEY # replace with "gemini-2.0-flash"
)

llm.bind_tools(tools)


console = Console()

# System prompt for the reservation assistant
system_prompt = """
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
chat_history = [
    SystemMessage(content=system_prompt)
]

def print_message(message, role):
    """Print messages in a nicely formatted way"""
    if role == "user":
        console.print(Panel(message, style="green", title="User", width=100))
    elif role == "assistant":
        md = Markdown(message)
        console.print(Panel(md, style="blue", title="Hotel Assistant", width=100))
    else:
        console.print(Panel(message, style="yellow", title=role, width=100))

def pretty_print_result(result, tool_name):
    """Print results in a nice format based on the tool used"""
    if tool_name == "check_availability":
        if not result:
            console.print("[bold red]No rooms found matching your criteria.[/bold red]")
            return
        
        console.print("[bold green]Available Rooms:[/bold green]")
        for room in result:
            console.print(Panel(
                f"[bold]Room {room['id']}[/bold]\n"
                f"Capacity: {room['capacity']} people\n"
                f"Features: {', '.join(room['features'])}",
                style="cyan"
            ))
    
    elif tool_name == "reserve_room":
        if result["status"] == "success":
            console.print(Panel(
                f"[bold green]Reservation Successful![/bold green]\n"
                f"Reservation ID: {result['reservation_id']}\n"
                f"Room: {result['details']['room_id']}\n"
                f"Guest: {result['details']['guest_name']}\n"
                f"Date: {result['details']['date']}\n"
                f"Time: {result['details']['start_time']} to {result['details']['end_time']}\n"
                f"Room Features: {', '.join(result['details']['features'])}",
                style="green"
            ))
        else:
            console.print(Panel(
                f"[bold red]Reservation Failed[/bold red]\n"
                f"Error: {result['message']}",
                style="red"
            ))

def extract_tool_call_from_text(text):
    """Extract tool call parameters from text when the LLM formats it as a string"""
    # Look for function call patterns
    check_pattern = r"check_availability\(([^)]+)\)"
    reserve_pattern = r"reserve_room\(([^)]+)\)"
    
    check_match = re.search(check_pattern, text)
    reserve_match = re.search(reserve_pattern, text)
    
    if check_match:
        params_str = check_match.group(1)
        tool_name = "check_availability"
    elif reserve_match:
        params_str = reserve_match.group(1)
        tool_name = "reserve_room"
    else:
        return None, None
    
    # Convert string parameters to a dictionary
    params = {}
    
    # Extract parameters based on the tool
    if tool_name == "check_availability":
        # Extract date
        date_match = re.search(r"date=['\"]([^'\"]+)['\"]", params_str)
        if date_match:
            params['date'] = date_match.group(1)
        
        # Extract start_time
        start_time_match = re.search(r"start_time=['\"]([^'\"]+)['\"]", params_str)
        if start_time_match:
            params['start_time'] = start_time_match.group(1)
        
        # Extract end_time
        end_time_match = re.search(r"end_time=['\"]([^'\"]+)['\"]", params_str)
        if end_time_match:
            params['end_time'] = end_time_match.group(1)
        
        # Extract capacity
        capacity_match = re.search(r"capacity=(\d+)", params_str)
        if capacity_match:
            params['capacity'] = int(capacity_match.group(1))
        
        # Extract features
        features_match = re.search(r"features=\[(.*?)\]", params_str)
        if features_match:
            features_str = features_match.group(1)
            # Extract quoted strings
            features = re.findall(r"['\"]([^'\"]+)['\"]", features_str)
            params['features'] = features
    
    elif tool_name == "reserve_room":
        # Extract room_id
        room_id_match = re.search(r"room_id=(\d+)", params_str)
        if room_id_match:
            params['room_id'] = int(room_id_match.group(1))
        
        # Extract guest_name
        guest_name_match = re.search(r"guest_name=['\"]([^'\"]+)['\"]", params_str)
        if guest_name_match:
            params['guest_name'] = guest_name_match.group(1)
        
        # Extract date
        date_match = re.search(r"date=['\"]([^'\"]+)['\"]", params_str)
        if date_match:
            params['date'] = date_match.group(1)
        
        # Extract start_time
        start_time_match = re.search(r"start_time=['\"]([^'\"]+)['\"]", params_str)
        if start_time_match:
            params['start_time'] = start_time_match.group(1)
        
        # Extract end_time
        end_time_match = re.search(r"end_time=['\"]([^'\"]+)['\"]", params_str)
        if end_time_match:
            params['end_time'] = end_time_match.group(1)
    
    return tool_name, params

def process_response(response_content):
    """Process the response from the LLM to handle tool calls"""
    # Check if it's already a structured tool call
    if isinstance(response_content, dict) and "tool_calls" in response_content:
        for tool_call in response_content["tool_calls"]:
            tool_name = tool_call["name"]
            try:
                params = json.loads(tool_call["args"])
                console.print(f"[italic yellow]Executing {tool_name} with parameters:[/italic yellow]")
                console.print(json.dumps(params, indent=2))
                
                if tool_name == "check_availability":
                    result = check_availability(params)
                elif tool_name == "reserve_room":
                    result = reserve_room(params)
                else:
                    console.print(f"[bold red]Unknown tool: {tool_name}[/bold red]")
                    return None, response_content
                
                pretty_print_result(result, tool_name)
                return result, response_content
            except Exception as e:
                console.print(f"[bold red]Error processing tool call: {e}[/bold red]")
    
    # If it's a string, try to extract tool call
    elif isinstance(response_content, str):
        tool_name, params = extract_tool_call_from_text(response_content)
        if tool_name and params:
            console.print(f"[italic yellow]Executing {tool_name} with parameters:[/italic yellow]")
            console.print(json.dumps(params, indent=2))
            
            try:
                if tool_name == "check_availability":
                    result = check_availability(params)
                elif tool_name == "reserve_room":
                    result = reserve_room(params)
                else:
                    console.print(f"[bold red]Unknown tool: {tool_name}[/bold red]")
                    return None, response_content
                
                pretty_print_result(result, tool_name)
                
                # Append the result to the original message
                updated_response = response_content + "\n\n**Results:**\n"
                
                if tool_name == "check_availability":
                    if not result:
                        updated_response += "No rooms found matching your criteria."
                    else:
                        updated_response += f"Found {len(result)} available room(s):\n"
                        for room in result:
                            updated_response += f"- Room {room['id']}: Capacity {room['capacity']}, Features: {', '.join(room['features'])}\n"
                
                elif tool_name == "reserve_room":
                    if result["status"] == "success":
                        updated_response += f"✅ Reservation confirmed! Reservation #{result['reservation_id']}\n"
                        updated_response += f"Room {result['details']['room_id']} has been reserved for {result['details']['guest_name']} on {result['details']['date']} from {result['details']['start_time']} to {result['details']['end_time']}."
                    else:
                        updated_response += f"❌ Reservation failed: {result['message']}"
                
                return result, updated_response
                
            except Exception as e:
                console.print(f"[bold red]Error executing tool: {e}[/bold red]")
    
    return None, response_content

def chat_loop():
    """Run an interactive chat loop"""
    console.print(Panel("Welcome to the Hotel Reservation Assistant!", style="bold blue"))
    console.print("Type 'exit' to end the conversation.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            console.print("[italic]Goodbye! Thank you for using the Hotel Reservation Assistant.[/italic]")
            break
        
        # Add user message to history
        chat_history.append(HumanMessage(content=user_input))
        print_message(user_input, "user")
        
        # Get response from LLM
        try:
            response = llm.invoke(chat_history)
            
            # Extract the content
            response_content = response.content if isinstance(response.content, str) else response.content.get("content", "")
            
            # Process any tool calls
            result, updated_response = process_response(response_content)
            
            # Display assistant's response
            print_message(updated_response, "assistant")
            
            # Add assistant message to history
            chat_history.append(AIMessage(content=updated_response))
            
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

# Example of how to test with predefined inputs
def test_with_examples():
    """Test the model with some example queries"""
    examples = [
        "I need a room for 4 people on May 11th from 2pm to 4pm.",
        "I'd like to book room 5 for tomorrow from 10am to 2pm. My name is John Smith.",
        "Are there any rooms with WiFi available on May 10th?",
        "I need a room with a mini-bar on May 10th for the afternoon.",
        "Can I reserve room 3 for May 15th from 9am to 5pm? My name is Alice Johnson."
    ]
    
    console.print(Panel("Running example queries", style="bold yellow"))
    
    for example in examples:
        console.print("\n[bold]Testing with query:[/bold]")
        print_message(example, "user")
        
        # Add user message to history
        chat_history.append(HumanMessage(content=example))
        
        # Get response from LLM
        try:
            response = llm.invoke(chat_history)
            
            # Extract the content
            response_content = response.content if isinstance(response.content, str) else response.content.get("content", "")
            
            # Process any tool calls
            result, updated_response = process_response(response_content)
            
            # Display assistant's response
            print_message(updated_response, "assistant")
            
            # Add assistant message to history
            chat_history.append(AIMessage(content=updated_response))
            
            console.print("[dim]Press Enter to continue...[/dim]")
            input()
            
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

# Main function to start the program
if __name__ == "__main__":
    console.print(Panel("Hotel Reservation System", style="bold blue", expand=False))
    console.print("1. Start interactive chat")
    console.print("2. Run example queries")
    choice = input("Select an option (1 or 2): ")
    
    if choice == "1":
        chat_loop()
    elif choice == "2":
        test_with_examples()
    else:
        console.print("[bold red]Invalid choice. Exiting.[/bold red]")