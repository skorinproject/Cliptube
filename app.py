import os
import requests
import subprocess
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# X-RAPIDAPI-KEY Kamu
RAPIDAPI_KEY = "11ba0effc0mshde6232632e2c60fp1928f9jsnda8b4c26e9ef"

def parse_time_to_seconds(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    except ValueError:
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
        return jsonify({'error': 'URL, waktu mulai, dan waktu selesai harus diisi!'}), 400

    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)

    if start_sec is None or end_sec is None or start_sec >= end_sec:
        return jsonify({'error': 'Format waktu tidak valid!'}), 400

    duration = end_sec - start_sec
    output_filename = f"video_trimmed_{start_sec}_{end_sec}.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)

    # 1. Dapatkan Direct Stream URL via RapidAPI
    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
    }
    
    try:
        # Ambil Video ID dari link YouTube
        video_id = url.split("v=")[-1].split("&")[0].split("/")[-1]
        response = requests.get(api_url, headers=headers, params={"videoId": video_id})
        res_data = response.json()

        # Ambil link stream video
        stream_url = None
        if "videos" in res_data and "items" in res_data["videos"] and len(res_data["videos"]["items"]) > 0:
            stream_url = res_data["videos"]["items"][0]["url"]
        
        if not stream_url:
            return jsonify({'error': 'Gagal mengambil link video dari YouTube API'}), 500

    except Exception as e:
        return jsonify({'error': f'Gagal menghubungi API: {str(e)}'}), 500

    # 2. Potong Video menggunakan FFmpeg langsung dari Stream URL
    cmd = [
        "ffmpeg",
        "-ss", str(start_sec),
        "-i", stream_url,
        "-t", str(duration),
        "-c", "copy",
        "-y",
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
                           
