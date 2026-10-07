from src.behaviour import (
    calculate_center,
    calculate_distance,
    is_inside_restricted_zone,
    check_loitering,
    check_unusual_movement,
    process_tracking_data
)


def test_calculate_center():
    result = calculate_center(100, 100, 200, 200)

    assert result == (150.0, 150.0)


def test_calculate_distance():
    result = calculate_distance(
        (100, 100),
        (200, 200)
    )

    assert round(result, 2) == 141.42


def test_restricted_zone():
    zone = {
        "x1": 100,
        "y1": 100,
        "x2": 400,
        "y2": 300
    }

    position = (250, 200)

    assert is_inside_restricted_zone(
        position,
        zone
    ) is True


def test_loitering():
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

    event = check_loitering(
        track_id=3,
        positions=positions,
        timestamps=timestamps
    )

    assert event is not None
    assert event["event"] == "Loitering"


def test_unusual_movement():
    event = check_unusual_movement(
        track_id=5,
        previous_position=(100, 100),
        current_position=(300, 300)
    )

    assert event is not None
    assert event["event"] == "Unusual Movement"


def test_tracking_behaviour_integration():
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

    assert len(events) > 0
    assert events[0]["track_id"] == 3
    assert events[0]["event"] == "Restricted Area Entry"