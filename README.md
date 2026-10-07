Warehouse Loitering & Safety Tracker

1. Project Overview

The Warehouse Loitering & Safety Tracker is a computer-vision-based system designed to monitor people inside warehouse environments.

The system processes warehouse video and aims to:

* Detect people in the video
* Track people across video frames
* Identify prolonged loitering
* Identify unusual movement
* Detect safety-related events
* Display the processed video through a Streamlit web interface

2. Problem Statement

Warehouses can contain restricted areas, machinery, storage zones, and other potentially unsafe locations. Manual monitoring of these areas can be difficult and may not identify unusual behaviour quickly.

This project provides an automated video-based monitoring approach to help identify potentially unsafe or unusual movement.

3. System Workflow

```text
Input Warehouse Video
        ↓
Person Detection
        ↓
Person Tracking
        ↓
Behaviour Analysis
        ↓
Safety Event Detection
        ↓
Processed Video + Events
        ↓
Streamlit Dashboard
```

4. Main Components

Person Detection

The detection module identifies people and their bounding boxes in each video frame using a YOLO-based object detection model.

File:

```text
src/detection.py
```

### Person Tracking

The tracking module assigns an ID to detected people and maintains their movement between frames.

File:

```text
src/tracking.py
```

Behaviour Analysis

The behaviour module analyses movement and time spent in an area to identify events such as loitering and unusual movement.

File:

```text
src/behaviour.py
```

Pipeline

The pipeline connects the detection and tracking components and processes the input video.

File:

```text
src/pipeline.py
```

Streamlit Interface

The Streamlit application provides a simple interface for uploading a warehouse video and viewing the processed result.

File:

```text
app.py
```

5. Technologies Used

* Python
* OpenCV
* YOLO / Ultralytics
* Streamlit
* Computer Vision
* Object Detection
* Object Tracking
* Behaviour Analysis

6. Project Structure

```text
PS07-Detection/
│
├── app.py
├── README.md
├── config/
│   └── zones.json
│
├── src/
│   ├── __init__.py
│   ├── detection.py
│   ├── tracking.py
│   ├── behaviour.py
│   └── pipeline.py
│
├── tests/
│
├── test_video.py
├── yolo_test.py
└── .gitignore
```

7. Installation

Install Python dependencies using:

```bash
pip install streamlit opencv-python ultralytics
```

If a `requirements.txt` file is provided in the final repository, install dependencies using:

```bash
pip install -r requirements.txt
```

8. Running the Application

Open a terminal in the project folder:

```bash
cd PS07-Detection
```

Run:

```bash
streamlit run app.py
```

The Streamlit interface will open in the browser.

Upload a supported warehouse video file and click:

```text
Process Video
```

9. Supported Video Formats

The application accepts:

* MP4
* AVI
* MOV
* MKV

10. Sample Input

A warehouse surveillance video containing people moving through the monitored area.

11. Sample Output

The system produces a processed video containing detected people with tracking IDs.

Example:

```text
Person ID: 1
Person ID: 2
Person ID: 3
```

Safety-related events can also be reported by the behaviour-analysis component.

12. Configuration

Behaviour and safety-related thresholds are stored in:

```text
config/zones.json
```

These configuration values can be adjusted according to the warehouse environment and monitoring requirements.

13. Scope

This project is a prototype designed for demonstration and hackathon purposes.

The system's results depend on video quality, camera position, detection accuracy, tracking performance, and configured thresholds.

It should not be considered a replacement for professional warehouse safety systems.

14. External Components

The project uses open-source software and pretrained computer-vision components, including:

* Ultralytics YOLO
* OpenCV
* Streamlit

The pretrained detection model is used for person detection.

## 15. Future Enhancements

* Real-time CCTV integration
* Improved multi-person tracking
* Configurable warehouse zones
* Real-time alerts
* Email/SMS notifications
* Safety-event dashboard
* Database-based event logging
* Improved behaviour classification

## 16. Team Contribution

### Role 1 — Detection

Developed the person-detection component.

### Role 2 — Tracking

Developed the person-tracking component.

### Role 3 — Behaviour Analysis

Developed behaviour and safety-event analysis.

### Role 4 — Pipeline & UI Integration

Integrated the modules and developed the Streamlit interface.

## 17. Disclaimer

This project is an educational/hackathon prototype intended to demonstrate computer-vision-based warehouse monitoring. Its outputs should be reviewed by humans before being used for operational safety decisions.
