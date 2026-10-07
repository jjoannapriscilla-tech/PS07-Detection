import json
import math
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "zones.json"


def load_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)


config = load_config()
restricted_zone = config["restricted_zone"]


# --------------------------------------------------
# POSITION CALCULATIONS
# --------------------------------------------------

def calculate_center(x1, y1, x2, y2):
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return center_x, center_y


def calculate_distance(previous_position, current_position):
    x1, y1 = previous_position
    x2, y2 = current_position

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


# --------------------------------------------------
# SAFETY EVENT CREATION
# --------------------------------------------------

def create_event(track_id, event_type, reason, timestamp=None):
    event = {
        "track_id": track_id,
        "event": event_type,
        "reason": reason,
        "timestamp": timestamp
    }

    return event


# --------------------------------------------------
# RESTRICTED ZONE DETECTION
# --------------------------------------------------

def is_inside_restricted_zone(position, zone):
    x, y = position

    return (
        zone["x1"] <= x <= zone["x2"]
        and
        zone["y1"] <= y <= zone["y2"]
    )


# --------------------------------------------------
# LOITERING DETECTION
# --------------------------------------------------

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

    if (
        time_spent >= config["loitering_time"]
        and
        movement <= config["loitering_radius"]
    ):
        return create_event(
            track_id,
            "Loitering",
            "Person remained in approximately the same area for too long",
            current_time
        )

    return None


# --------------------------------------------------
# UNUSUAL MOVEMENT DETECTION
# --------------------------------------------------

def check_unusual_movement(
    track_id,
    previous_position,
    current_position
):

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


# --------------------------------------------------
# TRACKING → BEHAVIOUR INTEGRATION
# --------------------------------------------------

def process_tracking_data(detections, timestamp, history):

    events = []

    for detection in detections:

        # Get Track ID from Person 2
        track_id = detection["track_id"]

        # Get bounding box from Person 1/Person 2
        box = detection["box"]

        # Calculate centre of the person
        center = calculate_center(
            box[0],
            box[1],
            box[2],
            box[3]
        )

        # Create history for a new person
        if track_id not in history:

            history[track_id] = {
                "positions": [],
                "timestamps": []
            }

        # Store current position
        history[track_id]["positions"].append(center)

        # Store current timestamp
        history[track_id]["timestamps"].append(timestamp)

        # --------------------------------------------------
        # CHECK 1: RESTRICTED ZONE
        # --------------------------------------------------

        if is_inside_restricted_zone(
            center,
            restricted_zone
        ):

            event = create_event(
                track_id,
                "Restricted Area Entry",
                "Person entered restricted zone",
                timestamp
            )

            events.append(event)

        # --------------------------------------------------
        # CHECK 2: LOITERING
        # --------------------------------------------------

        event = check_loitering(
            track_id,
            history[track_id]["positions"],
            history[track_id]["timestamps"]
        )

        if event:
            events.append(event)

        # --------------------------------------------------
        # CHECK 3: UNUSUAL MOVEMENT
        # --------------------------------------------------

        positions = history[track_id]["positions"]

        if len(positions) >= 2:

            previous_position = positions[-2]
            current_position = positions[-1]

            event = check_unusual_movement(
                track_id,
                previous_position,
                current_position
            )

            if event:
                events.append(event)

    return events


# ==================================================
# TESTING
# ==================================================

if __name__ == "__main__":

    print("\n--- BEHAVIOUR TESTING ---")

    # --------------------------------------------------
    # Test 1: Centre Calculation
    # --------------------------------------------------

    center = calculate_center(
        100,
        100,
        200,
        200
    )

    print("\n1. Centre Calculation")
    print("Centre:", center)


    # --------------------------------------------------
    # Test 2: Distance Calculation
    # --------------------------------------------------

    distance = calculate_distance(
        (100, 100),
        (200, 200)
    )

    print("\n2. Distance Calculation")
    print("Distance:", distance)


    # --------------------------------------------------
    # Test 3: Restricted Zone
    # --------------------------------------------------

    person_position = (250, 200)

    print("\n3. Restricted Zone")

    if is_inside_restricted_zone(
        person_position,
        restricted_zone
    ):

        print(
            "SAFETY EVENT: "
            "Person entered restricted zone"
        )

    else:

        print(
            "NORMAL: "
            "Person is outside restricted zone"
        )


    # --------------------------------------------------
    # Test 4: Loitering
    # --------------------------------------------------

    positions = [
        (250, 200),
        (252, 201),
        (251, 202),
        (250, 201)
    ]

    timestamps = [
        0,
        10,
        20,
        30
    ]

    print("\n4. Time Based Loitering Test")

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
        print("Timestamp:", event["timestamp"])

    else:

        print("No loitering detected")


    # --------------------------------------------------
    # Test 5: Unusual Movement
    # --------------------------------------------------

    previous_position = (100, 100)
    current_position = (300, 300)

    print("\n5. Unusual Movement Test")

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

        print("Normal movement")


    # --------------------------------------------------
    # Test 6: Tracking → Behaviour Integration
    # --------------------------------------------------

    print("\n6. Tracking → Behaviour Integration Test")

    # Example output coming from Person 2
    detections = [
        {
            "box": [250, 200, 270, 220],
            "track_id": 3
        }
    ]

    history = {}

    events = process_tracking_data(
        detections,
        timestamp=0,
        history=history
    )

    print("\nTracking data:")
    print(detections)

    print("\nBehaviour events:")

    if events:

        for event in events:

            print("Track ID:", event["track_id"])
            print("Event:", event["event"])
            print("Reason:", event["reason"])
            print("Timestamp:", event["timestamp"])

    else:

        print("No safety event")


    # --------------------------------------------------
    # Test 7: Multiple Time-Based Tracking
    # --------------------------------------------------

    print("\n7. Multiple Person Time-Based Test")

    people = {

        1: {
            "positions": [
                (50, 50),
                (80, 80),
                (120, 120)
            ],
            "timestamps": [
                0,
                10,
                20
            ]
        },

        2: {
            "positions": [
                (250, 200),
                (251, 201),
                (252, 200)
            ],
            "timestamps": [
                0,
                10,
                20
            ]
        },

        3: {
            "positions": [
                (150, 150),
                (155, 152),
                (160, 155)
            ],
            "timestamps": [
                0,
                10,
                30
            ]
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
            print("Timestamp:", event["timestamp"])

        else:

            print("Event: Normal movement")