import cv2
import tempfile

from src.detection import detect_objects
from src.tracking import PersonTracker
from src.behaviour import process_tracking_data


def process_video(input_path):

    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise ValueError("Could not open video")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )
    output_path = output_file.name
    output_file.close()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height)
    )

    tracker = PersonTracker()
    history = {}
    all_events = []

    frame_number = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_number += 1

        timestamp = frame_number / fps

        # Detection
        detections = detect_objects(frame)

        # Keep only persons
        person_detections = [
            detection
            for detection in detections
            if detection["class"] == "person"
        ]

        # Tracking
        tracked = tracker.update(person_detections)

        # Behaviour analysis
        events = process_tracking_data(
            tracked,
            timestamp,
            history
        )

        all_events.extend(events)

        # Draw results
        for detection in tracked:

            x1, y1, x2, y2 = detection["box"]
            track_id = detection["track_id"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Person {track_id}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        writer.write(frame)

    cap.release()
    writer.release()

    return output_path, all_events