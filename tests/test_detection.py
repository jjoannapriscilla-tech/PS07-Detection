import sys
sys.path.append(".")

from src.detection import detect_objects
import cv2

cap = cv2.VideoCapture("../testvideo1.mp4")

while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        break

    detections = detect_objects(frame)

    for detection in detections:
        print(detection)

cap.release()

print("Detection test completed!")