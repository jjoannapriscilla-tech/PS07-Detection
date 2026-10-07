from src.behaviour import (
    calculate_center,
    calculate_distance,
    is_inside_restricted_zone,
    check_loitering,
    check_unusual_movement
)

print("\n--- BEHAVIOUR TESTING ---")
# Test 1: Centre calculation
center = calculate_center(100, 100, 200, 200)
print("\n1. Centre Calculation")
print("Centre:", center)

distance = calculate_distance((100, 100),(200, 200))
print("\n2. Distance Calculation")
print("Distance:", distance)

zone = {"x1": 100,"y1": 100,"x2": 400,"y2": 300}
position = (250, 200)
print("\n3. Restricted Zone")
if is_inside_restricted_zone(position, zone):
    print("PASS: Person is inside restricted zone")
else:
    print("FAIL: Restricted zone detection")

positions = [(250, 200),(252, 201),(251, 202),(250, 201)]
timestamps = [0, 10, 20, 30]
event = check_loitering(
    track_id=3,
    positions=positions,
    timestamps=timestamps
)
print("\n4. Loitering")
if event:
    print("PASS: Loitering detected")
else:
    print("FAIL: Loitering not detected")

event = check_unusual_movement(
    track_id=5,
    previous_position=(100, 100),
    current_position=(300, 300)
)
print("\n5. Unusual Movement")
if event:
    print("PASS: Unusual movement detected")
else:
    print("FAIL: Unusual movement not detected")