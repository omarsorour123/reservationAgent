import sqlite3

import sqlite3
import json

# Connect to SQLite
conn = sqlite3.connect("hotel.db")
cursor = conn.cursor()

# Create the rooms table
cursor.execute('''
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY,
    capacity INTEGER NOT NULL,
    features TEXT
)
''')

# Create the reservations table (by time slots)
cursor.execute('''
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER,
    guest_name TEXT,
    date TEXT,          -- Format: YYYY-MM-DD
    start_time TEXT,    -- Format: HH:MM
    end_time TEXT,      -- Format: HH:MM
    FOREIGN KEY (room_id) REFERENCES rooms(id)
)
''')

# Insert sample room data
rooms = [
    (4, 2, json.dumps(['TV', 'WiFi', 'Ocean View'])),
    (5, 6, json.dumps(['TV', 'WiFi', 'Kitchen', 'AC', 'Pool Access'])),
    (6, 3, json.dumps(['TV', 'Mini-bar', 'Balcony'])),
    (7, 4, json.dumps(['WiFi', 'Kitchen', 'Pet Friendly'])),
    (8, 2, json.dumps(['TV', 'WiFi', 'Accessibility Features'])),
    (9, 8, json.dumps(['TV', 'WiFi', 'Conference Room', 'Projector'])),
    (10, 1, json.dumps(['WiFi', 'Work Desk', 'Coffee Machine']))
]
cursor.executemany("INSERT OR IGNORE INTO rooms (id, capacity, features) VALUES (?, ?, ?)", rooms)

# Insert sample reservation data (by time)
reservations = [
    (3, 'Charlie', '2025-05-10', '09:00', '11:00'),
    (4, 'David', '2025-05-10', '10:00', '18:00'),
    (5, 'Eve', '2025-05-10', '18:00', '22:00'),
    
    # May 11th reservations
    (1, 'Frank', '2025-05-11', '10:00', '12:00'),
    (2, 'Grace', '2025-05-11', '14:00', '16:00'),
    (6, 'Henry', '2025-05-11', '09:00', '17:00'),
    
    # May 12th reservations - high occupancy day
    (1, 'Irene', '2025-05-12', '08:00', '12:00'),
    (2, 'Jack', '2025-05-12', '09:00', '14:00'),
    (3, 'Kate', '2025-05-12', '10:00', '16:00'),
    (4, 'Leo', '2025-05-12', '11:00', '15:00'),
    (5, 'Mia', '2025-05-12', '14:00', '18:00'),
    (6, 'Noah', '2025-05-12', '16:00', '20:00'),
    (7, 'Olivia', '2025-05-12', '18:00', '22:00'),
    
    # May 15th - some reservations
    (9, 'Conference A', '2025-05-15', '09:00', '17:00'),
    (10, 'Pat', '2025-05-15', '13:00', '15:00')# overlapping times can be handled later
]
cursor.executemany('''
    INSERT INTO reservations (room_id, guest_name, date, start_time, end_time)
    VALUES (?, ?, ?, ?, ?)
''', reservations)

# Commit and close
conn.commit()
conn.close()



conn = sqlite3.connect("hotel.db")
cursor = conn.cursor()

cursor.execute("SELECT id, capacity, features FROM rooms")
for row in cursor.fetchall():
    room_id, capacity, features_json = row
    features = json.loads(features_json)
    print(f"Room {room_id}: Capacity={capacity}, Features={features}")

conn.close()
