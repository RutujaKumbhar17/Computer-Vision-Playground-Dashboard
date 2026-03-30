# Computer Vision Playground Dashboard

An interactive, educational dashboard for experimenting with computer vision algorithms in real-time. Built with Flask, OpenCV, and SocketIO.

## Features

- **Interactive Playground**: Test 10+ algorithms with real-time parameter tuning.
- **Custom Uploads**: Process your own images by clicking the "Upload Your Image" button.
- **Stereo Support**: Upload Left/Right pairs for depth mapping.
- **Download Results**: Save your processed experiments directly to your device.
- **Webcam Lab**: Stream and process live video from your camera using high-speed WebSockets.

## Algorithms Implemented

| Category | Algorithms |
| --- | --- |
| **Edge Detection** | Canny, Sobel, Laplacian |
| **Feature Analysis**| SIFT, ORB, Harris Corner Detection |
| **Matching** | BFMatcher, FLANN (Lowe's Ratio Test) |
| **Segmentation** | K-Means, Watershed |
| **Motion** | Lucas-Kanade, Farneback Optical Flow |
| **Depth** | Stereo Block Matching (BM), StereoSGBM |
| **Detection** | YOLOv8 Nano |

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "AI-Powered 3D Scene Reconstruction Dashboard"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the dashboard**:
   Open `http://localhost:5000` in your web browser.

## Project Structure

- `app.py`: Main Flask & SocketIO application.
- `src/cv_engine.py`: Core computer vision implementation.
- `src/demo_loader.py`: Handles sample images for the playground.
- `static/`: Frontend assets (CSS, JS, Images).
- `templates/`: Jinja2 HTML templates.
- `logs/`: System logs for debugging and metrics.

## Future Improvements

- Support for video file uploads with frame-by-frame analysis.
- Multi-algorithm side-by-side comparison view (A/B testing).
- Integration of custom Pytorch/TensorFlow models.
