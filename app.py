cat << 'EOF' > app.py
import os
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DOWNLOAD_FOLDER = '/sdcard/Movies'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def to_seconds(t):
    parts = list(map(int, t.strip().split(':')))
    if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2: return parts[0] * 60 + parts[1]
    return parts[0]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    start_sec = to_seconds(data.get('start'))
    end_sec = to_seconds(data.get('end'))
    res = data.get('resolution', '720')
    
    filename = f"clip_{res}p_{start_sec}_{end_sec}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    # Menentukan parameter format berdasarkan resolusi
    if res == '360':
        fmt = "bestvideo[height<=360]+bestaudio/18/best"
    elif res == '480':
        fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
    elif res == '720':
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    elif res == '1080_60':
        fmt = "bestvideo[height<=1080][fps>=60]+bestaudio/bestvideo[height<=1080]+bestaudio/best"
    else:
        fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    cmd = [
        "yt-dlp",
        "-f", fmt,
        "--download-sections", f"*{start_sec}-{end_sec}",
        "--merge-output-format", "mp4",
        "-o", filepath,
        url
    ]

    try:
        subprocess.run(cmd, check=True)
        # Refresh media scanner agar file masuk ke Galeri
        subprocess.run(["am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{filepath}"])
        return jsonify({"status": "sukses", "message": f"Berhasil diunduh ({res}p) ke folder Movies!"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Gagal mengunduh video."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
