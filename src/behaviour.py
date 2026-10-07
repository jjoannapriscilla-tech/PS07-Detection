import json
import math
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config" / "zones.json"


def load_config():
    """
    Load behaviour settings from zones.json.
    """

    with open(CONFIG_PATH, "r") as file:
        return json.load(file)


CONFIG = load_config()


def calculate_center(box):
    """
    Calculate the center point of a bounding box.
    """

    x1, y1, x2, y2 = box

    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return center_x, center_y


def calculate_distance(point1, point2):
    """
    Calculate Euclidean distance between two points.
    """

    return math.sqrt(
        (point1[0] - point2[0]) ** 2
        +
        (point1[1] - point2[1]) ** 2
    )


def create_event(track_id, event, reason, timestamp):
    """
    Create a behaviour event.
    """

    return {
        "track_id": track_id,
        "event": event,
        "reason": reason,
        "timestamp": timestamp
    }


def is_inside_restricted_zone(position, zone):
    """
    Check whether a person's center point is inside
    the selected rectangular restricted zone.
    """

    if zone is None:
        return False

    x1 = min(zone["x1"], zone["x2"])
    x2 = max(zone["x1"], zone["x2"])

    y1 = min(zone["y1"], zone["y2"])
    y2 = max(zone["y1"], zone["y2"])

    x, y = position

    return (
        x1 <= x <= x2
        and
        y1 <= y <= y2
    )


def check_loitering(track_history, current_time):
    """
    Determine whether a person is loitering.

    A person is considered loitering only when:

    1. They have been continuously tracked for a long time.
    2. Their total movement remains very small.
    3. They stay within a small area.
    4. The minimum loitering time is reached.

    This prevents a person who simply appears for a few seconds
    or moves normally from being classified as loitering.
    """

    loitering_time = CONFIG.get("loitering_time", 45)
    loitering_radius = CONFIG.get("loitering_radius", 40)

    timestamps = track_history["timestamps"]
    positions = track_history["positions"]

    if len(timestamps) < 2:
        return False

    time_spent = timestamps[-1] - timestamps[0]

    if time_spent < loitering_time:
        return False

    # Compare every recorded position with the first position.
    max_distance = 0

    first_position = positions[0]

    for position in positions:
        distance = calculate_distance(
            first_position,
            position
        )

        max_distance = max(
            max_distance,
            distance
        )

    # The person must remain inside a small movement radius.
    if max_distance <= loitering_radius:
        return True

    return False


def check_unusual_movement(track_history):
    """
    Detect unusually large movement between consecutive observations.
    """

    movement_threshold = CONFIG.get(
        "movement_threshold",
        100
    )

    positions = track_history["positions"]

    if len(positions) < 2:
        return False

    previous_position = positions[-2]
    current_position = positions[-1]

    movement = calculate_distance(
        previous_position,
        current_position
    )

    return movement > movement_threshold


def process_tracking_data(
    detections,
    timestamp,
    history,
    restricted_zone=None
):
    """
    Analyse tracked people and generate behaviour events.
    """

    events = []

    for detection in detections:

        track_id = detection["track_id"]

        position = calculate_center(
            detection["box"]
        )

        # Create history for a new person.
        if track_id not in history:

            history[track_id] = {
                "positions": [],
                "timestamps": [],
                "inside_zone": False,
                "restricted_zone_reported": False,
                "loitering_reported": False
            }

        track_history = history[track_id]

        # Store position and timestamp.
        track_history["positions"].append(position)
        track_history["timestamps"].append(timestamp)

        # Keep only recent history.
        # This prevents memory from growing forever.
        max_history = 300

        if len(track_history["positions"]) > max_history:

            track_history["positions"] = (
                track_history["positions"][-max_history:]
            )

            track_history["timestamps"] = (
                track_history["timestamps"][-max_history:]
            )

        # -------------------------------------------------
        # RESTRICTED AREA
        # -------------------------------------------------

        inside_zone = is_inside_restricted_zone(
            position,
            restricted_zone
        )

        previously_inside = track_history["inside_zone"]

        # Report only when the person ENTERS the zone.
        if (
            inside_zone
            and not previously_inside
            and not track_history["restricted_zone_reported"]
        ):

            events.append(
                create_event(
                    track_id,
                    "Restricted Area Entry",
                    "Person entered restricted zone",
                    timestamp
                )
            )

            track_history["restricted_zone_reported"] = True

        # When the person leaves the zone,
        # allow another entry event later.
        if not inside_zone:

            track_history["restricted_zone_reported"] = False

        track_history["inside_zone"] = inside_zone

        # -------------------------------------------------
        # LOITERING
        # -------------------------------------------------

        if not track_history["loitering_reported"]:

            if check_loitering(
                track_history,
                timestamp
            ):

                events.append(
                    create_event(
                        track_id,
                        "Loitering",
                        "Person remained in nearly the same area for an extended period",
                        timestamp
                    )
                )

                track_history["loitering_reported"] = True

        # -------------------------------------------------
        # UNUSUAL MOVEMENT
        # -------------------------------------------------

        if check_unusual_movement(track_history):

            events.append(
                create_event(
                    track_id,
                    "Unusual Movement",
                    "Person moved unusually far between observations",
                    timestamp
                )
            )

    return events