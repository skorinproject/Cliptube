import os
import requests
import subprocess
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

RAPIDAPI_KEY = "11ba0effc0mshde6232632e2c60fp1928f9jsnda8b4c26e9ef"

def get_youtube_video_id(url):
    if not url: return None
    url = url.strip()
    parsed = urlparse(url)
    if parsed.hostname == 'youtu.be':
        return parsed.path.lstrip('/')
    if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.path.startswith('/shorts/'):
            return parsed.path.split('/')[2]
    return None

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
    target_quality = data.get('quality', '1080')

    video_id = get_youtube_video_id(url)
    if not video_id:
        return jsonify({'error': 'URL YouTube tidak valid. Pastikan diawali https://'}), 400

    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)

    if start_sec is None or end_sec is None or start_sec >= end_sec:
        return jsonify({'error': 'Format waktu salah (Gunakan HH:MM:SS atau MM:SS)'}), 400

    duration = end_sec - start_sec
    output_filename = f"clip_{start_sec}_{end_sec}.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)

    # Ambil link dari RapidAPI
    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
    }

    try:
        response = requests.get(api_url, headers=headers, params={"videoId": video_id})
        res_data = response.json()

        stream_url = None
        formats = res_data.get("formats", []) or res_data.get("videos", {}).get("items", [])
        
        # Cari kualitas sesuai pilihan pengguna
        for fmt in formats:
            q = str(fmt.get("quality", "") or fmt.get("resolution", ""))
            if target_quality in q:
                stream_url = fmt.get("url")
                break
        
        # Jika tidak ketemu, pakai kualitas terbaik yang tersedia
        if not stream_url and formats:
            stream_url = formats[-1].get("url")

        if not stream_url:
            return jsonify({'error': 'Gagal mengambil stream video dari API.'}), 500

    except Exception as e:
        return jsonify({'error': f'Error API: {str(e)}'}), 500

    # Potong presisi dengan FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", stream_url,
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "ultrafast",
        "-avoid_negative_ts", "make_zero",
        output_filepath
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({'download_url': f'/get-file/{output_filename}'})
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Gagal memotong video dengan FFmpeg.'}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File tidak ditemukan'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
                
