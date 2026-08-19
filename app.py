import os
import subprocess
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def parse_time_to_seconds(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2: return parts[0] * 60 + parts[1]
        elif len(parts) == 1: return parts[0]
    except Exception:
        return None
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not url or not start_time or not end_time:
        return jsonify({'error': 'URL dan waktu wajib diisi!'}), 400

    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)

    if start_sec is None or end_sec is None or start_sec >= end_sec:
        return jsonify({'error': 'Format waktu salah (Gunakan HH:MM:SS atau MM:SS)'}), 400

    output_filename = f"clip_{start_sec}_{end_sec}.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)

    # yt-dlp memotong langsung dari server YouTube (Kilat, Hemat Kuota, Audio+Video 1080p Pas)
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080]+bestaudio/best",
        "--download-sections", f"*{start_sec}-{end_sec}",
        "--force-keyframes-at-cuts",
        "-o", output_filepath,
        url.strip()
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({'download_url': f'/get-file/{output_filename}'})
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Gagal mengambil video. Pastikan link YouTube benar.'}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File tidak ditemukan'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
