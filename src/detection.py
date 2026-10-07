from ultralytics import YOLO
import cv2
from pathlib import Path

# Load YOLO model
model = YOLO("yolo11n.pt")


def detect_objects(frame):
    results = model(frame)

    detections = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append({
                "class": model.names[class_id],
                "confidence": confidence,
                "box": [x1, y1, x2, y2]
            })

    return detections


if __name__ == "__main__":

    video_path = Path(__file__).parent.parent / "testvideo1.mp4"

    cap = cv2.VideoCapture(str(video_path))

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        detections = detect_objects(frame)

        for detection in detections:
            print(detection)

    cap.release()

    print("Detection completed!")