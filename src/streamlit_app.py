import streamlit as st
import requests
import uuid
import json
from datetime import datetime, timedelta
import pandas as pd

# API endpoint configuration
API_URL = "http://localhost:8000/api"  # Update this if your API is hosted elsewhere

# Set page configuration
st.set_page_config(
    page_title="Hotel Reservation Assistant",
    page_icon="🏨",
    layout="wide",
)

# Initialize session state variables if they don't exist
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "available_rooms" not in st.session_state:
    st.session_state.available_rooms = []

# Function to make API requests
def chat_with_assistant(message):
    """Send a message to the API and get the response."""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"thread_id": st.session_state.thread_id, "message": message},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def get_available_rooms(date, start_time, end_time, capacity=None, features=None):
    """Query available rooms directly through the API."""
    try:
        params = {
            "date": date,
            "start_time": start_time,
            "end_time": end_time
        }
        if capacity:
            params["capacity"] = capacity
        if features:
            params["features"] = features
            
        response = requests.post(
            f"{API_URL}/rooms/availability",
            json=params,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error checking room availability: {str(e)}")
        return []

def reserve_room(room_id, guest_name, date, start_time, end_time):
    """Reserve a room directly through the API."""
    try:
        response = requests.post(
            f"{API_URL}/rooms/reserve",
            json={
                "room_id": room_id,
                "guest_name": guest_name,
                "date": date,
                "start_time": start_time,
                "end_time": end_time
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error making reservation: {str(e)}")
        return {"status": "error", "message": str(e)}

# Sidebar for room search and booking
with st.sidebar:
    st.title("🏨 Room Finder")
    
    # Room search form
    with st.form("room_search"):
        st.subheader("Find Available Rooms")
        
        # Date selection (default to today)
        search_date = st.date_input(
            "Date", 
            value=datetime.now().date()
        )
        
        # Time range selection
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
        with col2:
            end_time = st.time_input("End Time", value=datetime.strptime("17:00", "%H:%M").time())
        
        # Capacity and features
        min_capacity = st.number_input("Minimum Capacity", min_value=1, value=1)
        
        feature_options = ["WiFi", "Projector", "Whiteboard", "Video Conferencing", "Catering"]
        selected_features = st.multiselect("Required Features", options=feature_options)
        
        search_button = st.form_submit_button("Search Rooms")
        
        if search_button:
            # Format date and times for API
            formatted_date = search_date.strftime("%Y-%m-%d")
            formatted_start = start_time.strftime("%H:%M")
            formatted_end = end_time.strftime("%H:%M")
            
            # Call API to get available rooms
            rooms = get_available_rooms(
                formatted_date, 
                formatted_start,
                formatted_end,
                min_capacity,
                selected_features if selected_features else None
            )
            
            st.session_state.available_rooms = rooms
            
            # Update the chat with search results
            if rooms:
                room_info = f"I found {len(rooms)} available rooms for {formatted_date} from {formatted_start} to {formatted_end}."
                chat_result = chat_with_assistant(room_info)
                if chat_result:
                    st.session_state.messages.append({"role": "user", "content": room_info})
                    st.session_state.messages.append({"role": "assistant", "content": chat_result["response"]})
            else:
                room_info = f"No rooms available for {formatted_date} from {formatted_start} to {formatted_end}."
                chat_result = chat_with_assistant(room_info)
                if chat_result:
                    st.session_state.messages.append({"role": "user", "content": room_info})
                    st.session_state.messages.append({"role": "assistant", "content": chat_result["response"]})
    
    # Display available rooms and booking option if rooms were found
    if st.session_state.available_rooms:
        st.subheader("Available Rooms")
        
        for room in st.session_state.available_rooms:
            with st.expander(f"Room {room['id']} (Capacity: {room['capacity']})"):
                st.write(f"Features: {', '.join(room['features'])}")
                
                # Booking form within each room expander
                with st.form(f"book_room_{room['id']}"):
                    st.subheader("Book This Room")
                    guest_name = st.text_input("Name", key=f"name_{room['id']}")
                    
                    book_button = st.form_submit_button("Book Room")
                    
                    if book_button:
                        if not guest_name:
                            st.error("Please enter your name")
                        else:
                            # Format date and times for reservation
                            formatted_date = search_date.strftime("%Y-%m-%d")
                            formatted_start = start_time.strftime("%H:%M")
                            formatted_end = end_time.strftime("%H:%M")
                            
                            # Make the reservation
                            reservation = reserve_room(
                                room['id'],
                                guest_name,
                                formatted_date,
                                formatted_start,
                                formatted_end
                            )
                            
                            if reservation["status"] == "success":
                                st.success("Room booked successfully!")
                                # Update the chat with reservation confirmation
                                confirmation = f"I've booked room {room['id']} for {guest_name} on {formatted_date} from {formatted_start} to {formatted_end}."
                                chat_result = chat_with_assistant(confirmation)
                                if chat_result:
                                    st.session_state.messages.append({"role": "user", "content": confirmation})
                                    st.session_state.messages.append({"role": "assistant", "content": chat_result["response"]})
                            else:
                                st.error(f"Booking failed: {reservation.get('message', 'Unknown error')}")
    
    # New conversation button
    if st.button("Start New Conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.available_rooms = []
        st.experimental_rerun()

# Main area for chat interface
st.title("Hotel Reservation Assistant")
st.info("👋 Welcome! I'm your AI hotel reservation assistant. Ask me about room availability or help with reservations.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat_with_assistant(user_input)
            if response:
                st.write(response["response"])
                st.session_state.messages.append({"role": "assistant", "content": response["response"]})
            else:
                st.error("Failed to get response from the assistant")

# Display conversation ID in footer
st.caption(f"Conversation ID: {st.session_state.thread_id}")