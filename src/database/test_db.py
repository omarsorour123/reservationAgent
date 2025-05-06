from database_operations import check_availability

def test_check_availability():
    print("Running availability tests...")
    
    # Test Case 1: Check for available rooms on May 10th afternoon
    # Expected: Some rooms should be available, but not rooms 1, 2, 3, 4, 5
    test1 = check_availability({
        'date': '2025-05-10',
        'start_time': '15:00',
        'end_time': '17:00',
        'capacity': 1
    })
    print("\nTest 1 - May 10th afternoon, min capacity 1:")
    print(f"Available rooms: {[room['id'] for room in test1]}")
    print(f"Expected unavailable: [1, 2, 3, 4, 5]")
    print(f"Test passed: {not any(room['id'] in [1, 2, 3, 4] for room in test1)}")
    
    # Test Case 2: Check for high-capacity room on May 11th
    # Expected: Room 5 (capacity 6), Room 9 (capacity 8) should be available
    test2 = check_availability({
        'date': '2025-05-11',
        'start_time': '10:00',
        'end_time': '12:00',
        'capacity': 6
    })
    print("\nTest 2 - May 11th morning, high capacity (6+):")
    print(f"Available rooms: {[room['id'] for room in test2]}")
    print(f"Expected available: [5, 9]")
    print(f"Test passed: {any(room['id'] == 5 for room in test2) and any(room['id'] == 9 for room in test2)}")
    
    # Test Case 3: Check for room with specific features
    # Expected: Room 7 (Pet Friendly) should be available on May 10th
    test3 = check_availability({
        'date': '2025-05-10',
        'start_time': '12:00',
        'end_time': '14:00',
        'features': ['Pet Friendly']
    })
    print("\nTest 3 - May 10th, with Pet Friendly feature:")
    print(f"Available rooms: {[room['id'] for room in test3]}")
    print(f"Expected available: [7]")
    print(f"Test passed: {any(room['id'] == 7 for room in test3)}")
    
    # Test Case 4: Check for available rooms on busy day (May 12th)
    # Expected: Few rooms available during busy hours
    test4 = check_availability({
        'date': '2025-05-12',
        'start_time': '12:00',
        'end_time': '14:00',
        'capacity': 2
    })
    print("\nTest 4 - May 12th (busy day), capacity 2+:")
    print(f"Available rooms: {[room['id'] for room in test4]}")
    print(f"Expected unavailable: [1, 2, 3, 4]")
    print(f"Test passed: {not any(room['id'] in [1, 2, 3, 4] for room in test4)}")
    
    # Test Case 5: Check for conference room features
    # Expected: Room 9 should be available on May 12th but not on May 15th
    test5a = check_availability({
        'date': '2025-05-12',
        'start_time': '09:00',
        'end_time': '17:00',
        'features': ['Conference Room']
    })
    test5b = check_availability({
        'date': '2025-05-15',
        'start_time': '09:00',
        'end_time': '17:00',
        'features': ['Conference Room']
    })
    print("\nTest 5 - Conference Room availability:")
    print(f"May 12th available rooms: {[room['id'] for room in test5a]}")
    print(f"May 15th available rooms: {[room['id'] for room in test5b]}")
    print(f"Test passed: {any(room['id'] == 9 for room in test5a) and not any(room['id'] == 9 for room in test5b)}")
    
    # Test Case 6: Check for non-existent date (should return all rooms)
    test6 = check_availability({
        'date': '2025-06-01',
        'start_time': '12:00',
        'end_time': '14:00'
    })
    print("\nTest 6 - Future date with no reservations:")
    print(f"Available rooms: {[room['id'] for room in test6]}")
    print(f"Expected: All 10 rooms")
    print(f"Test passed: {len(test6) == 10}")
    
    # Test Case 7: Check with impossible requirements
    # Expected: No rooms available
    test7 = check_availability({
        'date': '2025-05-12',
        'start_time': '12:00',
        'end_time': '14:00',
        'capacity': 10,
        'features': ['Pool Access', 'Pet Friendly']
    })
    print("\nTest 7 - Impossible requirements:")
    print(f"Available rooms: {[room['id'] for room in test7]}")
    print(f"Expected: No rooms")
    print(f"Test passed: {len(test7) == 0}")

# Run the tests
def test_boundary_conditions():
    print("\nTesting boundary conditions...")
    
    # Test Case 8: Edge case - booking immediately after another ends
    # Room 1 has a reservation on May 12th from 08:00-12:00
    test8 = check_availability({
        'date': '2025-05-12',
        'start_time': '12:00',  # Starting exactly when previous ends
        'end_time': '14:00',
        'capacity': 1
    })
    print("\nTest 8 - Booking immediately after another:")
    print(f"Is room 1 available: {any(room['id'] == 1 for room in test8)}")
    print(f"Test passed: {any(room['id'] == 1 for room in test8)}")
    
    # Test Case 9: Edge case - booking ends exactly when another starts
    # Room 2 has a reservation on May 11th from 14:00-16:00
    test9 = check_availability({
        'date': '2025-05-11',
        'start_time': '12:00',
        'end_time': '14:00',  # Ending exactly when next starts
        'capacity': 1
    })
    print("\nTest 9 - Booking ends exactly when another starts:")
    print(f"Is room 2 available: {any(room['id'] == 2 for room in test9)}")
    print(f"Test passed: {any(room['id'] == 2 for room in test9)}")
    
    # Test Case 10: Verify overlapping bookings are properly detected
    # Room 2 has a reservation on May 11th from 14:00-16:00
    test10 = check_availability({
        'date': '2025-05-11',
        'start_time': '13:00',  # Overlaps with existing reservation
        'end_time': '15:00',
        'capacity': 1
    })
    print("\nTest 10 - Overlapping booking:")
    print(f"Is room 2 available: {any(room['id'] == 2 for room in test10)}")
    print(f"Test passed: {not any(room['id'] == 2 for room in test10)}")

# Run the additional tests
test_check_availability()
test_boundary_conditions()