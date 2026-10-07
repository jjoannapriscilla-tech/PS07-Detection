import cv2
import tempfile
import subprocess
import math
from pathlib import Path

import imageio_ffmpeg

from src.detection import detect_objects, reset_tracker
from src.behaviour import process_tracking_data


# -------------------------------------------------
# PERFORMANCE SETTINGS
# -------------------------------------------------

# Run YOLO on every 2nd frame.
#
# Example:
# 30 FPS video
# -> YOLO processes approximately 15 frames/sec
#
FRAME_SKIP = 2


# -------------------------------------------------
# STABLE ID SETTINGS
# -------------------------------------------------

# Maximum distance in pixels used to reconnect
# a new ByteTrack ID with a recently seen person.
ID_MATCH_DISTANCE = 120


# Keep the person's display ID alive for this
# many frames if ByteTrack temporarily loses them.
ID_MEMORY_FRAMES = 60


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------

def calculate_center(box):

    x1, y1, x2, y2 = box

    return (
        (x1 + x2) / 2,
        (y1 + y2) / 2
    )


def calculate_distance(point1, point2):

    return math.sqrt(
        (point1[0] - point2[0]) ** 2
        +
        (point1[1] - point2[1]) ** 2
    )


# -------------------------------------------------
# VIDEO PROCESSING
# -------------------------------------------------

def process_video(
    input_path,
    restricted_zone=None,
    display_id_map=None
):
    """
    Process the warehouse video.

    YOLO runs every 2nd frame to reduce CPU load.

    Stable display IDs are maintained separately
    from ByteTrack's internal IDs.
    """

    input_path = str(input_path)

    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():

        raise RuntimeError(
            "Could not open the input video."
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    # -------------------------------------------------
    # RESET TRACKER
    # -------------------------------------------------

    reset_tracker()

    # -------------------------------------------------
    # TEMPORARY VIDEO
    # -------------------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    temp_path = temp_file.name

    temp_file.close()

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        temp_path,
        fourcc,
        fps,
        (width, height)
    )

    # -------------------------------------------------
    # BEHAVIOUR DATA
    # -------------------------------------------------

    history = {}

    events = []

    # -------------------------------------------------
    # DISPLAY ID DATA
    # -------------------------------------------------

    if display_id_map is None:
        display_id_map = {}

    # Memory of recently seen people.
    #
    # This helps when ByteTrack changes its
    # internal tracker ID.

    person_memory = {}

    next_display_id = 1

    # -------------------------------------------------
    # FRAME DATA
    # -------------------------------------------------

    frame_number = 0

    # Most recent YOLO detections.
    #
    # These are reused on skipped frames.
    last_detections = []

    # -------------------------------------------------
    # PROCESS VIDEO
    # -------------------------------------------------

    while cap.isOpened():

        ret, frame = cap.read()

        if not ret:
            break

        frame_number += 1

        timestamp = (
            frame_number / fps
        )

        # -------------------------------------------------
        # RUN YOLO EVERY 2ND FRAME
        # -------------------------------------------------

        if frame_number % FRAME_SKIP == 1:

            detections = detect_objects(
                frame
            )

            # Save latest detections.
            last_detections = detections

        else:

            # Reuse latest detections.
            detections = last_detections

        # -------------------------------------------------
        # ASSIGN STABLE DISPLAY IDS
        # -------------------------------------------------

        current_display_ids = set()

        for detection in detections:

            tracker_id = (
                detection["track_id"]
            )

            center = calculate_center(
                detection["box"]
            )

            # ---------------------------------------------
            # NO TRACK ID
            # ---------------------------------------------

            if tracker_id is None:

                detection["display_id"] = (
                    "Detecting..."
                )

                continue

            # ---------------------------------------------
            # EXISTING BYTE TRACK ID
            # ---------------------------------------------

            if tracker_id in display_id_map:

                display_id = (
                    display_id_map[
                        tracker_id
                    ]
                )

            else:

                # -----------------------------------------
                # TRY TO MATCH WITH A RECENT PERSON
                # -----------------------------------------

                best_display_id = None

                best_distance = float(
                    "inf"
                )

                for (
                    old_display_id,
                    memory
                ) in person_memory.items():

                    # Do not assign the same
                    # person twice in one frame.

                    if (
                        old_display_id
                        in current_display_ids
                    ):
                        continue

                    frames_missing = (
                        frame_number
                        -
                        memory["last_seen"]
                    )

                    # Person disappeared too long.
                    if (
                        frames_missing
                        >
                        ID_MEMORY_FRAMES
                    ):
                        continue

                    distance = (
                        calculate_distance(
                            center,
                            memory["center"]
                        )
                    )

                    if (
                        distance
                        <
                        ID_MATCH_DISTANCE
                        and
                        distance
                        <
                        best_distance
                    ):

                        best_distance = (
                            distance
                        )

                        best_display_id = (
                            old_display_id
                        )

                # -----------------------------------------
                # EXISTING PERSON FOUND
                # -----------------------------------------

                if best_display_id is not None:

                    display_id = (
                        best_display_id
                    )

                    display_id_map[
                        tracker_id
                    ] = display_id

                # -----------------------------------------
                # COMPLETELY NEW PERSON
                # -----------------------------------------

                else:

                    display_id = (
                        next_display_id
                    )

                    display_id_map[
                        tracker_id
                    ] = display_id

                    next_display_id += 1

            # ---------------------------------------------
            # UPDATE PERSON MEMORY
            # ---------------------------------------------

            person_memory[
                display_id
            ] = {

                "center": center,

                "last_seen": frame_number,

                "tracker_id": tracker_id
            }

            current_display_ids.add(
                display_id
            )

            detection["display_id"] = (
                display_id
            )

        # -------------------------------------------------
        # REMOVE OLD PEOPLE FROM MEMORY
        # -------------------------------------------------

        old_people = []

        for (
            display_id,
            memory
        ) in person_memory.items():

            if (
                frame_number
                -
                memory["last_seen"]
                >
                ID_MEMORY_FRAMES
            ):

                old_people.append(
                    display_id
                )

        for display_id in old_people:

            del person_memory[
                display_id
            ]

        # -------------------------------------------------
        # BEHAVIOUR ANALYSIS
        # -------------------------------------------------

        tracked_detections = [

            detection

            for detection in detections

            if detection["track_id"] is not None
        ]

        frame_events = (
            process_tracking_data(

                tracked_detections,

                timestamp,

                history,

                restricted_zone
            )
        )

        # -------------------------------------------------
        # ADD DISPLAY ID TO EVENTS
        # -------------------------------------------------

        for event in frame_events:

            tracker_id = (
                event["track_id"]
            )

            person_id = (
                display_id_map.get(
                    tracker_id
                )
            )

            if person_id is not None:

                event["display_id"] = (
                    person_id
                )

                events.append(
                    event
                )

        # -------------------------------------------------
        # DRAW RESTRICTED ZONE
        # -------------------------------------------------

        if restricted_zone is not None:

            zx1 = int(
                min(
                    restricted_zone["x1"],
                    restricted_zone["x2"]
                )
            )

            zy1 = int(
                min(
                    restricted_zone["y1"],
                    restricted_zone["y2"]
                )
            )

            zx2 = int(
                max(
                    restricted_zone["x1"],
                    restricted_zone["x2"]
                )
            )

            zy2 = int(
                max(
                    restricted_zone["y1"],
                    restricted_zone["y2"]
                )
            )

            cv2.rectangle(

                frame,

                (zx1, zy1),

                (zx2, zy2),

                (0, 0, 255),

                3
            )

            cv2.putText(

                frame,

                "RESTRICTED AREA",

                (
                    zx1,
                    max(
                        30,
                        zy1 - 10
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 0, 255),

                2
            )

        # -------------------------------------------------
        # DRAW PERSON BOXES
        # -------------------------------------------------

        for detection in detections:

            x1, y1, x2, y2 = (
                detection["box"]
            )

            confidence = (
                detection["confidence"]
            )

            person_id = (
                detection["display_id"]
            )

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                2
            )

            if person_id == "Detecting...":

                label = (
                    f"Person | "
                    f"{confidence:.2f}"
                )

            else:

                label = (
                    f"Person {person_id} | "
                    f"{confidence:.2f}"
                )

            cv2.putText(

                frame,

                label,

                (
                    x1,
                    max(
                        25,
                        y1 - 8
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,

                (0, 255, 0),

                2
            )

        # -------------------------------------------------
        # WRITE FRAME
        # -------------------------------------------------

        writer.write(frame)

    # -------------------------------------------------
    # RELEASE
    # -------------------------------------------------

    cap.release()

    writer.release()

    # -------------------------------------------------
    # CONVERT TO H264
    # -------------------------------------------------

    output_file = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    output_path = output_file.name

    output_file.close()

    ffmpeg_exe = (
        imageio_ffmpeg.get_ffmpeg_exe()
    )

    command = [

        ffmpeg_exe,

        "-y",

        "-i",

        temp_path,

        "-c:v",

        "libx264",

        "-pix_fmt",

        "yuv420p",

        "-movflags",

        "+faststart",

        output_path
    ]

    result = subprocess.run(

        command,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE
    )

    if result.returncode != 0:

        try:

            Path(temp_path).unlink()

        except Exception:

            pass

        raise RuntimeError(
            "FFmpeg could not create the final video."
        )

    # -------------------------------------------------
    # DELETE TEMPORARY FILE
    # -------------------------------------------------

    try:

        Path(temp_path).unlink()

    except Exception:

        pass

    # -------------------------------------------------
    # RETURN RESULTS
    # -------------------------------------------------

    return (

        output_path,

        events,

        display_id_map
    )