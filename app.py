import streamlit as st
import cv2
import tempfile
from PIL import Image
from streamlit_image_coordinates import (
    streamlit_image_coordinates
)

from src.pipeline import process_video


st.set_page_config(
    page_title="Warehouse Security Analyzer",
    page_icon="🎥",
    layout="wide"
)


st.title("🎥 Warehouse Security Video Analyzer")

st.write(
    "Upload a video, select the restricted area, "
    "and analyze people, tracking and behaviour."
)


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------

if "zone_points" not in st.session_state:
    st.session_state.zone_points = []

if "zone_selector_key" not in st.session_state:
    st.session_state.zone_selector_key = 0

if "last_click_time" not in st.session_state:
    st.session_state.last_click_time = None

if "display_id_map" not in st.session_state:
    st.session_state.display_id_map = {}


# -------------------------------------------------
# VIDEO UPLOAD
# -------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a warehouse video",
    type=["mp4", "avi", "mov", "mkv"]
)


if uploaded_file is not None:

    # -------------------------------------------------
    # SAVE UPLOADED VIDEO
    # -------------------------------------------------

    temp_input = tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False
    )

    temp_input.write(
        uploaded_file.getbuffer()
    )

    temp_input.close()

    input_path = temp_input.name

    # -------------------------------------------------
    # READ FIRST FRAME
    # -------------------------------------------------

    cap = cv2.VideoCapture(
        input_path
    )

    ret, first_frame = cap.read()

    cap.release()

    if not ret:

        st.error(
            "Could not read the first frame of the video."
        )

        st.stop()

    # OpenCV BGR -> RGB
    first_frame_rgb = cv2.cvtColor(
        first_frame,
        cv2.COLOR_BGR2RGB
    )

    original_height, original_width = (
        first_frame_rgb.shape[:2]
    )

    # -------------------------------------------------
    # DISPLAY SIZE
    # -------------------------------------------------

    max_display_width = 900

    if original_width > max_display_width:

        display_width = max_display_width

        scale = (
            display_width /
            original_width
        )

        display_height = int(
            original_height * scale
        )

        display_frame = cv2.resize(
            first_frame_rgb,
            (display_width, display_height)
        )

    else:

        display_frame = first_frame_rgb

        display_width = original_width
        display_height = original_height

        scale = 1.0

    # -------------------------------------------------
    # RESTRICTED ZONE SELECTION
    # -------------------------------------------------

    st.subheader(
        "Step 1 — Select the Restricted Area"
    )

    st.info(
        "Click the TOP-LEFT corner of the restricted "
        "area, then click the BOTTOM-RIGHT corner."
    )

    clicked = streamlit_image_coordinates(
        display_frame,
        key=(
            f"zone_selector_"
            f"{st.session_state.zone_selector_key}"
        )
    )

    # -------------------------------------------------
    # HANDLE CLICK
    # -------------------------------------------------

    if clicked is not None:

        click_time = clicked.get(
            "unix_time"
        )

        if click_time != st.session_state.last_click_time:

            st.session_state.last_click_time = click_time

            clicked_x = int(
                clicked["x"] / scale
            )

            clicked_y = int(
                clicked["y"] / scale
            )

            if len(
                st.session_state.zone_points
            ) < 2:

                st.session_state.zone_points.append(
                    (clicked_x, clicked_y)
                )

    # -------------------------------------------------
    # SHOW SELECTED POINTS
    # -------------------------------------------------

    if len(st.session_state.zone_points) == 1:

        x, y = st.session_state.zone_points[0]

        st.success(
            f"First point selected: ({x}, {y})"
        )

        st.write(
            "Now click the bottom-right corner."
        )

    elif len(st.session_state.zone_points) == 2:

        x1, y1 = st.session_state.zone_points[0]
        x2, y2 = st.session_state.zone_points[1]

        st.success(
            "Restricted area selected."
        )

        # Draw a preview of the selected zone.
        preview = first_frame_rgb.copy()

        cv2.rectangle(
            preview,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            4
        )

        cv2.putText(
            preview,
            "RESTRICTED AREA",
            (
                min(x1, x2),
                max(30, min(y1, y2) - 10)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 0, 0),
            3
        )

        st.image(
            preview,
            caption="Selected Restricted Area",
            width="stretch"
        )

    # -------------------------------------------------
    # RESET ZONE
    # -------------------------------------------------

    if st.button(
        "🔄 Reset Restricted Area"
    ):

        st.session_state.zone_points = []

        st.session_state.last_click_time = None

        st.session_state.zone_selector_key += 1

        st.rerun()

    # -------------------------------------------------
    # PROCESS BUTTON
    # -------------------------------------------------

    if len(
        st.session_state.zone_points
    ) == 2:

        st.divider()

        st.subheader(
            "Step 2 — Analyze Video"
        )

        if st.button(
            "▶️ Start Video Analysis",
            type="primary"
        ):

            x1, y1 = st.session_state.zone_points[0]
            x2, y2 = st.session_state.zone_points[1]

            restricted_zone = {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            }

            # Reset display IDs for this analysis.
            st.session_state.display_id_map = {}

            with st.spinner(
                "Analyzing video... Please wait."
            ):

                try:

                    output_path, events, id_map = (
                        process_video(
                            input_path,
                            restricted_zone,
                            st.session_state.display_id_map
                        )
                    )

                except Exception as error:

                    st.error(
                        f"Video processing failed: {error}"
                    )

                    st.stop()

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            st.success(
                "Video analysis completed!"
            )

            st.subheader(
                "Processed Video"
            )

            with open(
                output_path,
                "rb"
            ) as video_file:

                video_bytes = (
                    video_file.read()
                )

            st.video(
                video_bytes
            )

            # -------------------------------------------------
            # EVENTS
            # -------------------------------------------------

            st.subheader(
                "Detected Events"
            )

            if not events:

                st.success(
                    "No behaviour events detected."
                )

            else:

                for event in events:

                    display_id = event.get(
                        "display_id",
                        event["track_id"]
                    )

                    timestamp = event[
                        "timestamp"
                    ]

                    st.warning(
                        f"Person {display_id} — "
                        f"{event['event']} — "
                        f"{event['reason']} — "
                        f"{timestamp:.1f}s"
                    )