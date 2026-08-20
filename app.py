import os
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Simpan langsung ke folder Download internal HP
DOWNLOAD_FOLDER = '/sdcard/Download'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def parse_time_to_seconds(time_str):
    if not time_str: return None
    try:
        parts = list(map(int, time_str.strip().split(':')))
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
    url = data.get('url', '').strip()
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not url or not start_time or not end_time:
        return jsonify({'error': 'URL dan waktu wajib diisi!'}), 400

    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)

    if start_sec is None or end_sec is None or start_sec >= end_sec:
        return jsonify({'error': 'Format waktu salah!'}), 400

    output_filename = f"clip_{start_sec}_{end_sec}.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)

    # Perintah yt-dlp aman dari 403 Forbidden & hemat kuota (-f 18 + mweb)
    cmd = [
        "yt-dlp",
        "-f", "18",
        "--extractor-args", "youtube:player_client=mweb",
        "--download-sections", f"*{start_sec}-{end_sec}",
        "-o", output_filepath,
        url
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({'message': f'Berhasil! File tersimpan di folder Download dengan nama {output_filename}'})
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Gagal mengambil video. Pastikan link YouTube benar.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
