import os
import subprocess
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def parse_time_to_seconds(time_str):
    if not time_str:
        return None
    try:
        parts = list(map(int, time_str.strip().split(':')))
        if len(parts) == 3: 
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2: 
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1: 
            return parts[0]
    except Exception:
        return None
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url', '').strip()
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    quality = data.get('quality', '1080')

    if not url or not start_time or not end_time:
        return jsonify({'error': 'URL dan waktu wajib diisi!'}), 400

    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)

    if start_sec is None or end_sec is None or start_sec >= end_sec:
        return jsonify({'error': 'Format waktu salah! Gunakan format 03:58 atau 00:03:58'}), 400

    output_filename = f"clip_{start_sec}_{end_sec}.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)

    # Bersihkan file lama jika ada
    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    # Sesuaikan format kualitas sesuai pilihan dropdown UI
    if quality == 'best':
        fmt_str = "bestvideo+bestaudio/best"
    else:
        fmt_str = f"bestvideo[height<={quality}]+bestaudio/best"

    cmd = [
        "yt-dlp",
        "-f", fmt_str,
        "--download-sections", f"*{start_sec}-{end_sec}",
        "--force-keyframes-at-cuts",
        "-o", output_filepath,
        url
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({'download_url': f'/get-file/{output_filename}'})
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Gagal mengambil video. Pastikan jaringan stabil & link benar.'}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File tidak ditemukan'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
