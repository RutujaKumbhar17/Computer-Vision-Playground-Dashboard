import os
import cv2
import base64
import numpy as np
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from src.cv_engine import engine
from src.demo_loader import demo_loader
from src.logger import logger

START_TIME = time.time()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cv_playground_secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

from werkzeug.utils import secure_filename

try:
    import psutil
except ImportError:
    psutil = None

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    """Home page routing."""
    return render_template('index.html')

@app.route('/playground/<category>')
def playground(category):
    """Algorithm playground interface."""
    return render_template('playground.html', category=category)

@app.route('/webcam')
def webcam():
    """Real-time webcam interface."""
    return render_template('webcam.html')

@app.route('/api/upload', methods=['POST'])
def upload_api():
    """API for uploading custom images."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file:
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({
            "status": "success",
            "filename": filename,
            "url": f"/uploads/{filename}"
        })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/telemetry')
def telemetry_api():
    """Returns system health metrics for the dashboard."""
    try:
        if psutil:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
        else:
            cpu, ram = 0, 0
            
        return jsonify({
            "status": "success",
            "cpu": cpu,
            "ram": ram,
            "uptime": int(time.time() - START_TIME)
        })
    except Exception as e:
        logger.error(f"Telemetry API error: {str(e)}")
        return jsonify({"status": "success", "cpu": 0, "ram": 0, "uptime": 0})

@app.route('/api/process', methods=['POST'])
def process_api():
    """Main API for processing images with algorithm selection and parameters."""
    try:
        data = request.json
        category = data.get('category')
        method = data.get('method')
        params = data.get('params', {})
        uploaded_filename = data.get('uploaded_filename')
        
        # Load image (demo or uploaded)
        if uploaded_filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_filename)
            img = cv2.imread(path)
        else:
            img = demo_loader.get_demo_image(category)
            
        if img is None:
            return jsonify({"status": "error", "message": "High-precision engine failed to initialize image source"}), 400
        
        metrics = {}
        output = img
        
        # Dispatch to CV Engine with Precision focus
        if category == 'edge':
            output = engine.edge_detection(img, method, **params)
        elif category == 'features':
            output, metrics = engine.feature_detection(img, method, **params)
        elif category == 'segmentation':
            output = engine.segmentation(img, method, **params)
        elif category == 'detection':
            conf = params.get('conf_thresh', 0.25) / 100.0 if 'conf_thresh' in params else 0.25
            output, metrics = engine.object_detection(img, conf_thresh=conf)
        elif category == 'stereo':
            # Mock right image with a horizontal shift for depth estimation
            right_img = np.roll(img, 15, axis=1)
            output = engine.stereo_depth(img, right_img, method, **params)
        
        # Encode for transport (Industry Standard JPEG quality)
        _, buffer = cv2.imencode('.jpg', output, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        base64_str = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            "status": "success",
            "image": f"data:image/jpeg;base64,{base64_str}",
            "metrics": metrics
        })
    except Exception as e:
        logger.error(f"Industrial Engine Error: {str(e)}")
        return jsonify({"status": "error", "message": f"Engine Fault: {str(e)}"}), 500

@socketio.on('process_frame')
def handle_frame(data):
    """Handle incoming webcam frames via SocketIO."""
    try:
        # Decode frame
        header, encoded = data['image'].split(",", 1)
        decoded = base64.b64decode(encoded)
        nparr = np.frombuffer(decoded, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        method = data.get('method', 'edge')
        
        # Process frame
        if method == 'edge':
            processed = engine.edge_detection(frame, 'canny')
        elif method == 'features':
            processed, _ = engine.feature_detection(frame, 'orb')
        elif method == 'detection':
            processed, _ = engine.object_detection(frame)
        else:
            processed = frame
            
        # Encode and emit back
        _, buffer = cv2.imencode('.jpg', processed)
        base64_out = base64.b64encode(buffer).decode('utf-8')
        emit('response_frame', {'image': f"data:image/jpeg;base64,{base64_out}"})
        
    except Exception as e:
        logger.error(f"Socket Handler Error: {str(e)}")

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
