cat << 'EOF' > app.py
import os
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
# Ubah lokasi simpan ke folder Movies agar terbaca CapCut & Galeri
DOWNLOAD_FOLDER = '/sdcard/Movies'

def to_seconds(t):
    parts = list(map(int, t.strip().split(':')))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
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

    if res == '360':
        fmt = "18/best[height<=360]"
    elif res == '480':
        fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]"
    elif res == '720':
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif res == '1080_60':
        fmt = "bestvideo[height<=1080][fps>=60]+bestaudio/bestvideo[height<=1080]+bestaudio/best"
    else:
        fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"

    output_file = os.path.join(DOWNLOAD_FOLDER, f"clip_{res}p_{start_sec}_{end_sec}.mp4")

    cmd = [
        "yt-dlp",
        "-f", fmt,
        "--extractor-args", "youtube:player_client=mweb",
        "--download-sections", f"*{start_sec}-{end_sec}",
        "--merge-output-format", "mp4",
        "-o", output_file,
        url
    ]

    try:
        subprocess.run(cmd, check=True)
        # Pemicu otomatis pemindaian media Android
        subprocess.run(["am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{output_file}"])
        return jsonify({"status": "sukses", "message": f"Berhasil! Video tersimpan di folder Movies."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Gagal mengunduh video."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
        
