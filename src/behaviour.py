import json
import math
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
CONFIG_PATH=BASE_DIR/"config"/"zones.json"
def load_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)
def calculate_center(x1, y1, x2, y2):
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y
def calculate_distance(previous_position, current_position):
    x1, y1 = previous_position
    x2, y2 = current_position
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def create_event(track_id, event_type, reason, timestamp=None):
    event = {
        "track_id": track_id,
        "event": event_type,
        "reason": reason,
        "timestamp": timestamp
    }
    return event

def check_loitering(track_id, positions, timestamps):
    if not positions or not timestamps:
        return None
    start_position = positions[0]
    current_position = positions[-1]
    start_time = timestamps[0]
    current_time = timestamps[-1]
    time_spent = current_time - start_time
    movement = calculate_distance(
        start_position,
        current_position
    )
    if time_spent >= config["loitering_time"] and movement <= config["loitering_radius"]:
        return create_event(
            track_id,
            "Loitering",
            "Person remained in approximately the same area for too long"
        )
    return None

def check_unusual_movement(track_id, previous_position, current_position):
    movement = calculate_distance(
        previous_position,
        current_position
    )
    if movement > config["movement_threshold"]:
        return create_event(
            track_id,
            "Unusual Movement",
            "Person moved an unusually large distance"
        )
    return None

def is_inside_restricted_zone(position,zone):
    x,y = position
    return(
        zone["x1"]<=x<=zone["x2"] and zone["y1"]<=y<=zone["y2"]
    )

config = load_config()
restricted_zone = config["restricted_zone"]
person_position=(250, 200)
if is_inside_restricted_zone(person_position, restricted_zone):
    print("SAFETY EVENT: Person entered restricted zone")
else:
    print("NORMAL: Person is outside restricted zone")

LOITERING_TIME = config["loitering_time"]
positions = [(250, 200),(252, 201),(251, 202),(250, 201),(252, 200)]
print("\nChecking for loitering...")
total_movement = 0
for i in range(1, len(positions)):
    movement = calculate_distance(positions[i - 1], positions[i])
    total_movement += movement
print("Total movement:", total_movement)

event = create_event(
    track_id=3,
    event_type="Loitering",
    reason="Person remained in approximately the same area for too long"
)
print("\nSafety Event:")
print("Track ID:", event["track_id"])
print("Event:", event["event"])
print("Reason:", event["reason"])

print("\n--- Multiple Person Time-Based Test ---")
people = {
    1: {
        "positions": [(50, 50), (80, 80), (120, 120)],
        "timestamps": [0, 10, 20]
    },
    2: {
        "positions": [(250, 200), (251, 201), (252, 200)],
        "timestamps": [0, 10, 20]
    },
    3: {
        "positions": [(150, 150), (155, 152), (160, 155)],
        "timestamps": [0, 10, 30]
    }
}
for track_id, person in people.items():
    event = check_loitering(
        track_id,
        person["positions"],
        person["timestamps"]
    )
    print("\nTrack ID:", track_id)
    if event:
        print("Event:", event["event"])
        print("Reason:", event["reason"])
    else:
        print("Event: Normal movement")

print("\n--- Time Based Loitering Test ---")
positions = [(250, 200),(252, 201),(251, 202),(250, 201)]
timestamps = [0,10,20,30]
event = check_loitering(
    track_id=3,
    positions=positions,
    timestamps=timestamps
)
if event:
    print("\nSafety Event:")
    print("Track ID:", event["track_id"])
    print("Event:", event["event"])
    print("Reason:", event["reason"])
else:
    print("\nNo loitering detected")

print("\n--- Unusual Movement Test ---")
previous_position = (100, 100)
current_position = (300, 300)
event = check_unusual_movement(
    track_id=5,
    previous_position=previous_position,
    current_position=current_position
)
if event:
    print("\nSafety Event:")
    print("Track ID:", event["track_id"])
    print("Event:", event["event"])
    print("Reason:", event["reason"])
else:
    print("\nNormal movement")

print("\n--- Event Timestamp Test ---")
event = create_event(
    track_id=3,
    event_type="Loitering",
    reason="Person remained in approximately the same area for too long",
    timestamp=30
)
print("\nSafety Event:")
print("Track ID:", event["track_id"])
print("Event:", event["event"])
print("Reason:", event["reason"])
print("Timestamp:", event["timestamp"], "seconds")

