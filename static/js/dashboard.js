// Global State
let socket;
let uploadedFilename = null;
let debounceTimer;
let latencyChart;
let latencyData = [];

const paramConfigs = {
    'edge': [
        { name: 'low_thresh', label: 'Canny Low Threshold', min: 0, max: 255, value: 100 },
        { name: 'high_thresh', label: 'Canny High Threshold', min: 0, max: 255, value: 200 },
        { name: 'kernel_size', label: 'Sobel Kernel Size', min: 3, max: 7, value: 3, step: 2 }
    ],
    'features': [
        { name: 'n_features', label: 'Keypoint Capacity', min: 100, max: 2000, value: 500 }
    ],
    'segmentation': [
        { name: 'k', label: 'Precision K-Clusters', min: 2, max: 20, value: 5 }
    ],
    'stereo': [
        { name: 'num_disparities', label: 'Disparity Mapping Range', min: 16, max: 128, value: 64 },
        { name: 'block_size', label: 'Correlation Block Size', min: 5, max: 51, value: 15 }
    ],
    'detection': [
        { name: 'conf_thresh', label: 'Confidence Sensitivity', min: 5, max: 95, value: 25 }
    ] 
};

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    startTelemetry();
    
    if (typeof CATEGORY !== 'undefined') {
        renderParams(CATEGORY);
        updateProcessing();
    }
    
    if (window.location.pathname === '/webcam') {
        initWebcam();
    }
});

function initCharts() {
    const ctx = document.getElementById('latencyChart');
    if (!ctx) return;
    
    latencyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(20).fill(''),
            datasets: [{
                label: 'LATENCY (MS)',
                data: Array(20).fill(0),
                borderColor: '#10b981',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(16, 185, 129, 0.05)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { display: false, min: 0 },
                x: { display: false }
            }
        }
    });
}

function startTelemetry() {
    setInterval(() => {
        fetch('/api/telemetry')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('sys-cpu').innerText = data.cpu + '%';
                document.getElementById('sys-ram').innerText = data.ram + '%';
                document.getElementById('sys-uptime').innerText = data.uptime + 's';
                
                // Active indicators
                document.getElementById('sys-core').style.color = '#10b981';
            }
        })
        .catch(() => {
            document.getElementById('sys-core').style.color = '#ef4444';
            document.getElementById('sys-core').innerText = 'OFFLINE';
        });
    }, 2000);
}

function renderParams(category) {
    const container = document.getElementById('dynamic-params');
    if (!container) return;
    
    container.innerHTML = '';
    const config = paramConfigs[category] || [];
    
    config.forEach(param => {
        const div = document.createElement('div');
        div.className = 'param-group';
        div.style.marginBottom = '1.5rem';
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">
                <label>${param.label}</label>
                <span id="val-${param.name}" style="color: var(--primary); font-family: 'JetBrains Mono'; font-weight: 700;">${param.value}${param.name === 'conf_thresh' ? '%' : ''}</span>
            </div>
            <input type="range" name="${param.name}" min="${param.min}" max="${param.max}" value="${param.value}" step="${param.step || 1}"
                   oninput="document.getElementById('val-${param.name}').innerText = this.value + (this.name === 'conf_thresh' ? '%' : ''); debouncedUpdate()">
        `;
        container.appendChild(div);
    });
}

function debouncedUpdate() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(updateProcessing, 300);
}

function updateProcessing() {
    const methodSelect = document.getElementById('method-select');
    if (!methodSelect) return;
    
    const method = methodSelect.value;
    const inputs = document.querySelectorAll('#dynamic-params input');
    const params = {};
    inputs.forEach(input => params[input.name] = parseInt(input.value));
    
    const loading = document.getElementById('loading-spinner');
    if (loading) loading.style.display = 'flex';
    
    const startTime = performance.now();
    
    fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            category: CATEGORY, 
            method, 
            params,
            uploaded_filename: uploadedFilename
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('output-img').src = data.image;
            const lat = Math.round(performance.now() - startTime);
            document.getElementById('stat-time').innerText = lat + 'ms';
            
            // Update Latency Chart
            if (latencyChart) {
                latencyChart.data.datasets[0].data.push(lat);
                latencyChart.data.datasets[0].data.shift();
                latencyChart.update('none');
            }
            
            // Update metrics
            const metricMap = {
                'features': 'keypoints',
                'matching': 'matches',
                'detection': 'objects'
            };
            const metricKey = metricMap[CATEGORY] || null;
            if (metricKey && data.metrics[metricKey]) {
                document.getElementById('stat-kp').innerText = data.metrics[metricKey];
            } else {
                document.getElementById('stat-kp').innerText = '--';
            }

            // Enable download
            const dBtn = document.getElementById('download-btn');
            if (dBtn) dBtn.disabled = false;
        } else {
            console.error("Inference Error:", data.message);
        }
    })
    .catch(err => console.error(err))
    .finally(() => {
        if (loading) loading.style.display = 'none';
    });
}

function handleFileUpload(input) {
    if (!input.files || !input.files[0]) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    
    const badge = document.getElementById('status-badge');
    badge.innerHTML = '<i class="fas fa-microchip fa-spin"></i> SYNCING ASSET...';
    
    fetch('/api/upload', { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            uploadedFilename = data.filename;
            document.getElementById('input-img').src = data.url;
            badge.innerHTML = '<i class="fas fa-check-double" style="color: #10b981;"></i> ASSET_ID: ' + data.filename.substring(0,8);
            updateProcessing();
        }
    });
}

function downloadResult() {
    const img = document.getElementById('output-img');
    const link = document.createElement('a');
    link.href = img.src;
    link.download = `VISION_EXPORT_${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Webcam Lab Logic
function initWebcam() {
    const video = document.getElementById('webcam-feed');
    const canvas = document.createElement('canvas');
    const outImg = document.getElementById('live-processed');
    socket = io();
    
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(stream => {
        video.srcObject = stream;
        video.play();
        
        setInterval(() => {
            const context = canvas.getContext('2d');
            canvas.width = 640;
            canvas.height = 480;
            context.drawImage(video, 0, 0, 640, 480);
            const data = canvas.toDataURL('image/jpeg', 0.5);
            const method = document.getElementById('webcam-method').value;
            socket.emit('process_frame', { image: data, method });
        }, 150); 
    });
    
    socket.on('response_frame', data => {
        const signal = document.getElementById('no-signal');
        if (signal) signal.style.display = 'none';
        outImg.src = data.image;
    });
}
