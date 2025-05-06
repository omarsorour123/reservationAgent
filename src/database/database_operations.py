import sqlite3
import json

conn = sqlite3.connect("hotel.db")
cursor = conn.cursor()  


def check_availability(query_parameters):
    """
    Check for available rooms based on query parameters.
    
    Parameters:
    query_parameters (dict): A dictionary containing search criteria such as:
        - date (str): Date in format 'YYYY-MM-DD'
        - start_time (str): Start time in format 'HH:MM'
        - end_time (str): End time in format 'HH:MM'
        - capacity (int): Minimum capacity required
        - features (list): List of required features
    
    Returns:
    list: List of available room IDs matching the criteria
    """
    conn = sqlite3.connect("hotel.db")
    cursor = conn.cursor()
    
    # Extract parameters with defaults
    date = query_parameters.get('date')
    start_time = query_parameters.get('start_time')
    end_time = query_parameters.get('end_time')
    min_capacity = query_parameters.get('capacity', 1)
    required_features = query_parameters.get('features', [])
    
    # Base query to get all rooms meeting capacity requirement
    query = """
    SELECT r.id, r.capacity, r.features 
    FROM rooms r
    WHERE r.capacity >= ?
    """
    params = [min_capacity]
    
    # If time constraints specified, filter out rooms with reservations that conflict
    if date and start_time and end_time:
        query = """
        SELECT r.id, r.capacity, r.features 
        FROM rooms r
        WHERE r.capacity >= ?
        AND r.id NOT IN (
            SELECT room_id 
            FROM reservations 
            WHERE date = ?
            AND NOT (end_time <= ? OR start_time >= ?)
        )
        """
        params = [min_capacity, date, start_time, end_time]
    
    # Execute query
    cursor.execute(query, params)
    available_rooms = []
    
    # Process results
    for room_id, capacity, features_json in cursor.fetchall():
        features = json.loads(features_json)
        
        # Check if room has all required features
        if required_features:
            has_all_features = all(feature in features for feature in required_features)
            if not has_all_features:
                continue
        
        # Add room to available rooms
        available_rooms.append({
            "id": room_id,
            "capacity": capacity,
            "features": features
        })
    
    conn.close()
    return available_rooms


def reserve_room(reservation_data):
    """
    Reserve a room based on provided data.
    
    Parameters:
    reservation_data (dict): A dictionary containing reservation details:
        - room_id (int): The ID of the room to reserve
        - guest_name (str): Name of the guest
        - date (str): Date in format 'YYYY-MM-DD'
        - start_time (str): Start time in format 'HH:MM'
        - end_time (str): End time in format 'HH:MM'
    
    Returns:
    dict: Result of the reservation with status and reservation ID if successful
    """
    try:
        conn = sqlite3.connect("hotel.db")
        cursor = conn.cursor()
        
        # Extract parameters
        room_id = reservation_data.get('room_id')
        guest_name = reservation_data.get('guest_name')
        date = reservation_data.get('date')
        start_time = reservation_data.get('start_time')
        end_time = reservation_data.get('end_time')
        
        # Validate required fields
        if not all([room_id, guest_name, date, start_time, end_time]):
            return {
                "status": "error",
                "message": "Missing required reservation information"
            }
        
        # Check if the room exists
        cursor.execute("SELECT id FROM rooms WHERE id = ?", (room_id,))
        if not cursor.fetchone():
            return {
                "status": "error",
                "message": f"Room {room_id} does not exist"
            }
        
        # Check if the room is available during the requested time
        cursor.execute("""
            SELECT id FROM reservations 
            WHERE room_id = ? AND date = ? 
            AND NOT (end_time <= ? OR start_time >= ?)
        """, (room_id, date, start_time, end_time))
        
        if cursor.fetchone():
            return {
                "status": "error",
                "message": f"Room {room_id} is not available during the requested time"
            }
        
        # Insert the reservation
        cursor.execute("""
            INSERT INTO reservations (room_id, guest_name, date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
        """, (room_id, guest_name, date, start_time, end_time))
        
        # Get the reservation ID
        reservation_id = cursor.lastrowid
        
        # Commit the changes
        conn.commit()
        
        # Get room details to include in response
        cursor.execute("SELECT capacity, features FROM rooms WHERE id = ?", (room_id,))
        room_data = cursor.fetchone()
        capacity = room_data[0]
        features = json.loads(room_data[1])
        
        conn.close()
        
        return {
            "status": "success",
            "reservation_id": reservation_id,
            "message": f"Room {room_id} reserved successfully for {guest_name} on {date} from {start_time} to {end_time}",
            "details": {
                "room_id": room_id,
                "capacity": capacity,
                "features": features,
                "guest_name": guest_name,
                "date": date,
                "start_time": start_time,
                "end_time": end_time
            }
        }
        
    except Exception as e:
        if conn:
            conn.close()
        return {
            "status": "error",
            "message": f"Error making reservation: {str(e)}"
        }