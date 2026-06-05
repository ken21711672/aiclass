from flask import Flask, send_from_directory
from flask_cors import CORS
import socket
import os

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

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
    local_ip = get_local_ip()
    port = 5000
    print(f'\n{"="*45}')
    print(f'  UniFi Signal Analyzer — Local Server')
    print(f'{"="*45}')
    print(f'  電腦瀏覽器：http://localhost:{port}')
    print(f'  手機（同一 Wi-Fi）：http://{local_ip}:{port}')
    print(f'{"="*45}')
    print(f'  按 Ctrl+C 停止伺服器\n')
    app.run(host='0.0.0.0', port=port, debug=False)
