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
# BASIC CALCULATIONS
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
# EVENT CREATION
# --------------------------------------------------

def create_event(track_id, event_type, reason, timestamp=None):
    return {
        "track_id": track_id,
        "event": event_type,
        "reason": reason,
        "timestamp": timestamp
    }


# --------------------------------------------------
# RESTRICTED ZONE CHECK
# --------------------------------------------------

def is_inside_restricted_zone(position, zone):
    x, y = position

    return (
        zone["x1"] <= x <= zone["x2"]
        and
        zone["y1"] <= y <= zone["y2"]
    )


# --------------------------------------------------
# LOITERING CHECK
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
# UNUSUAL MOVEMENT CHECK
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
# MAIN BEHAVIOUR ANALYSIS
# --------------------------------------------------

def process_tracking_data(detections, timestamp, history):

    events = []

    for detection in detections:

        track_id = detection["track_id"]
        box = detection["box"]

        # ------------------------------------------
        # Calculate person's center
        # ------------------------------------------

        center = calculate_center(
            box[0],
            box[1],
            box[2],
            box[3]
        )

        # ------------------------------------------
        # Create history for new person
        # ------------------------------------------

        if track_id not in history:

            history[track_id] = {
                "positions": [],
                "timestamps": [],
                "inside_zone": False,
                "restricted_zone_reported": False,
                "loitering_reported": False
            }

        # ------------------------------------------
        # Store position and timestamp
        # ------------------------------------------

        history[track_id]["positions"].append(center)
        history[track_id]["timestamps"].append(timestamp)

        # ------------------------------------------
        # Restricted zone detection
        # ------------------------------------------

        inside_zone = is_inside_restricted_zone(
            center,
            restricted_zone
        )

        previously_inside = history[track_id]["inside_zone"]

        if (
            inside_zone
            and not previously_inside
            and not history[track_id]["restricted_zone_reported"]
        ):

            event = create_event(
                track_id,
                "Restricted Area Entry",
                "Person entered restricted zone",
                timestamp
            )

            events.append(event)

            # Report only once for this track
            history[track_id]["restricted_zone_reported"] = True

        # Update current zone status
        history[track_id]["inside_zone"] = inside_zone

        # ------------------------------------------
        # Loitering detection
        # ------------------------------------------

        if not history[track_id]["loitering_reported"]:

            event = check_loitering(
                track_id,
                history[track_id]["positions"],
                history[track_id]["timestamps"]
            )

            if event:
                events.append(event)

                # Report loitering only once
                history[track_id]["loitering_reported"] = True

        # ------------------------------------------
        # Unusual movement detection
        # ------------------------------------------

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


# --------------------------------------------------
# BASIC TESTING
# --------------------------------------------------

if __name__ == "__main__":

    print("Testing behaviour analysis...")

    # Test center
    center = calculate_center(
        10, 20, 30, 40
    )

    print("Center:", center)

    # Test distance
    distance = calculate_distance(
        (10, 20),
        (20, 30)
    )

    print("Distance:", distance)

    # Test restricted zone
    test_position = (
        (restricted_zone["x1"] + restricted_zone["x2"]) / 2,
        (restricted_zone["y1"] + restricted_zone["y2"]) / 2
    )

    inside = is_inside_restricted_zone(
        test_position,
        restricted_zone
    )

    print("Inside restricted zone:", inside)

    # Test event
    event = create_event(
        1,
        "Test Event",
        "Testing behaviour module",
        5.0
    )

    print("Test event:", event)

    print("Behaviour tests completed!")