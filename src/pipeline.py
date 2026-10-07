import cv2
import tempfile
import subprocess
import os
import imageio_ffmpeg

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

    # Temporary OpenCV video
    temp_video = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )
    temp_video_path = temp_video.name
    temp_video.close()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = cv2.VideoWriter(
        temp_video_path,
        fourcc,
        fps,
        (width, height)
    )

    if not writer.isOpened():
        cap.release()
        raise ValueError("Could not create output video")

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

        # Keep only people
        person_detections = [
            d for d in detections
            if d["class"] == "person"
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

        # Draw tracking results
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

    # Convert to browser-friendly H.264 MP4
    output_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )
    output_path = output_file.name
    output_file.close()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg,
        "-y",
        "-i",
        temp_video_path,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        output_path
    ]

    subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

    # Remove temporary OpenCV video
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)

    return output_path, all_events