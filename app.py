import os
import subprocess
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def parse_time_to_seconds(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
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
    url = data.get('url')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    quality = data.get('quality', '720')

    if not url or not start_time or not end_time:
        return jsonify({'error': 'URL, waktu mulai, dan waktu selesai wajib diisi!'}), 400

    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)

    if start_sec is None or end_sec is None or start_sec >= end_sec:
        return jsonify({'error': 'Format waktu tidak valid!'}), 400

    output_filename = f"video_trimmed_{start_sec}_{end_sec}.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)

    format_option = f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best"

    cmd = [
    "yt-dlp",
    "--extractor-args", "youtube:player_client=android,web",
    "--force-overwrites",
    "-f", format_option,
    "--download-sections", f"*{start_sec}-{end_sec}",
    "-o", output_filepath,
    url
]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({'download_url': f'/get-file/{output_filename}'})
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Gagal memproses video. Pastikan link valid.'}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File tidak ditemukan'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

