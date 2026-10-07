from ultralytics import YOLO

# Load YOLO model
model = YOLO("yolo11n.pt")

# Run detection on the factory video
results = model.predict(
    source="Example of Hi-Definition Video Surveillance of a Factory Floor - by CCTVDOC.COM.mp4",
    show=True,
    save=True,
    conf=0.4
)

print("Detection completed!")