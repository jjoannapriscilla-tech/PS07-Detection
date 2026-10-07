from src.tracking import PersonTracker


def test_new_person_gets_id():
    tracker = PersonTracker()

    detections = [
        {
            "class": "person",
            "box": [100, 100, 150, 200],
            "confidence": 0.95
        }
    ]

    result = tracker.update(detections)

    assert result[0]["track_id"] == 1


def test_two_people_get_different_ids():
    tracker = PersonTracker()

    detections = [
        {
            "class": "person",
            "box": [100, 100, 150, 200],
            "confidence": 0.95
        },
        {
            "class": "person",
            "box": [400, 100, 450, 200],
            "confidence": 0.90
        }
    ]

    result = tracker.update(detections)

    assert result[0]["track_id"] != result[1]["track_id"]


def test_same_person_keeps_id():
    tracker = PersonTracker()

    first_frame = [
        {
            "class": "person",
            "box": [100, 100, 150, 200],
            "confidence": 0.95
        }
    ]

    first_result = tracker.update(first_frame)
    first_id = first_result[0]["track_id"]

    second_frame = [
        {
            "class": "person",
            "box": [105, 105, 155, 205],
            "confidence": 0.94
        }
    ]

    second_result = tracker.update(second_frame)

    assert second_result[0]["track_id"] == first_id