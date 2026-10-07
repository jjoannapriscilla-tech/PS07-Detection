import streamlit as st
import tempfile
import os

from src.pipeline import process_video


st.set_page_config(
    page_title="Warehouse Loitering & Safety Tracker",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Warehouse Loitering & Safety Tracker")

st.write(
    "Upload a warehouse video to detect people, track their movement, "
    "and identify unusual safety-related behaviour."
)

st.divider()

st.header("📹 Upload Warehouse Video")

uploaded_video = st.file_uploader(
    "Choose a video file",
    type=["mp4", "avi", "mov", "mkv"]
)

if uploaded_video is not None:

    st.success("Video uploaded successfully!")

    st.video(uploaded_video)

    if st.button("▶ Process Video", type="primary"):

        with st.spinner("Processing video..."):

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp4"
            ) as temp_file:

                temp_file.write(uploaded_video.read())
                input_path = temp_file.name

            try:
                output_path, events = process_video(input_path)

                st.success("✅ Video processing completed!")

                st.subheader("🎬 Processed Video")

                with open(output_path, "rb") as video_file:
                    st.video(video_file.read())

                st.subheader("🚨 Safety Events")

                if events:
                    for event in events:
                        st.warning(str(event))
                else:
                    st.success("No safety events detected.")

            except Exception as e:
                st.error(f"Processing failed: {e}")

            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)

else:
    st.info("Please upload a warehouse video to begin.")