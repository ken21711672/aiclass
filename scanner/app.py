from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import numpy as np
import base64
import socket

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    data = request.files['image'].read()
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({'error': 'Invalid image'}), 400

    floor_plan = generate_floor_plan(img)

    _, buf = cv2.imencode('.png', floor_plan)
    b64 = base64.b64encode(buf).decode('utf-8')
    return jsonify({'floor_plan': f'data:image/png;base64,{b64}'})


def generate_floor_plan(img):
    # ── 1. Resize to fixed width for consistent processing ──────────────────
    h, w = img.shape[:2]
    target_w = 900
    scale = target_w / w
    img = cv2.resize(img, (target_w, int(h * scale)))
    h, w = img.shape[:2]

    # ── 2. Greyscale + denoise ───────────────────────────────────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # ── 3. Canny edge detection ──────────────────────────────────────────────
    edges = cv2.Canny(gray, 40, 120, apertureSize=3)

    # ── 4. Dilate edges to close small gaps ─────────────────────────────────
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # ── 5. Probabilistic Hough line transform ────────────────────────────────
    min_len = max(w, h) // 8   # ignore very short lines (furniture edges)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=60,
        minLineLength=min_len,
        maxLineGap=30,
    )

    # ── 6. Draw onto a clean white canvas ───────────────────────────────────
    canvas = np.full((h, w, 3), 248, dtype=np.uint8)  # near-white background

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            # Keep only lines that are roughly horizontal or vertical (walls)
            is_horizontal = angle < 18 or angle > 162
            is_vertical   = 72 < angle < 108
            if is_horizontal or is_vertical:
                cv2.line(canvas, (x1, y1), (x2, y2), (30, 30, 30), 3)

    # ── 7. Overlay faint edge hint for non-orthogonal details ───────────────
    edge_overlay = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    canvas = cv2.addWeighted(canvas, 0.92, edge_overlay, 0.08, 0)

    # ── 8. Label ─────────────────────────────────────────────────────────────
    cv2.putText(canvas, 'Auto Floor Plan (OpenCV)', (10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1)

    return canvas


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'localhost'


if __name__ == '__main__':
    ip = get_local_ip()
    port = 5001
    print(f'\n{"="*48}')
    print(f'  Room Scanner — Floor Plan Generator')
    print(f'{"="*48}')
    print(f'  電腦：  http://localhost:{port}')
    print(f'  手機：  http://{ip}:{port}')
    print(f'{"="*48}')
    print(f'  Ctrl+C 停止\n')
    app.run(host='0.0.0.0', port=port, debug=False)
