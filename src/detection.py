from ultralytics import YOLO


# -------------------------------------------------
# MODEL
# -------------------------------------------------

MODEL_PATH = "yolo11s.pt"

model = YOLO(MODEL_PATH)


# -------------------------------------------------
# RESET TRACKER
# -------------------------------------------------

def reset_tracker():
    """
    Reset the tracker before processing a new video.
    """

    try:
        model.predictor = None
    except Exception:
        pass


# -------------------------------------------------
# DETECTION + TRACKING
# -------------------------------------------------

def detect_objects(frame):
    """
    Detect and track people using YOLO11s + ByteTrack.

    Settings are chosen to balance:
    - better detection of people at the edges
    - reasonable CPU processing speed
    """

    results = model.track(
        source=frame,

        persist=True,

        # Use standard Ultralytics ByteTrack
        tracker="bytetrack.yaml",

        # Slightly lower confidence helps detect
        # partially visible people.
        conf=0.20,

        iou=0.50,

        # Person class only
        classes=[0],

        # Keep 640 for better detection
        # than the previous 512 setting.
        imgsz=640,

        verbose=False
    )

    detections = []

    for result in results:

        if result.boxes is None:
            continue

        boxes = result.boxes

        coordinates = (
            boxes.xyxy.cpu().tolist()
        )

        confidences = (
            boxes.conf.cpu().tolist()
        )

        classes = (
            boxes.cls.int().cpu().tolist()
        )

        if boxes.id is not None:

            track_ids = (
                boxes.id.int()
                .cpu()
                .tolist()
            )

        else:

            track_ids = [
                None
                for _ in coordinates
            ]

        for (
            box,
            confidence,
            class_id,
            track_id
        ) in zip(
            coordinates,
            confidences,
            classes,
            track_ids
        ):

            if class_id != 0:
                continue

            x1, y1, x2, y2 = map(
                int,
                box
            )

            if x2 <= x1 or y2 <= y1:
                continue

            detections.append(
                {
                    "class": "person",

                    "confidence": float(
                        confidence
                    ),

                    "box": [
                        x1,
                        y1,
                        x2,
                        y2
                    ],

                    "track_id": (
                        int(track_id)
                        if track_id is not None
                        else None
                    )
                }
            )

    return detections