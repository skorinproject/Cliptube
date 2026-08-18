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
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed.path == '/watch': return parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.path.startswith('/shorts/'): return parsed.path.split('/')[2]
    elif parsed.hostname == 'youtu.be': return parsed.path[1:]
    return None

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_id = get_youtube_video_id(data.get('url'))
    
    # 1. Panggil API dengan parameter kualitas
    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    headers = {"x-rapidapi-key": RAPIDAPI_KEY}
    
    response = requests.get(api_url, headers=headers, params={"videoId": video_id})
    res_data = response.json()

    # 2. Logika pilih stream 1080p
    stream_url = None
    formats = res_data.get("formats", [])
    
    # Cari yang ada tulisannya 1080
    for fmt in formats:
        if "1080" in str(fmt.get("quality", "")):
            stream_url = fmt.get("url")
            break
    
    # Kalau gak ada 1080, cari yang terbaik (terakhir)
    if not stream_url and formats:
        stream_url = formats[-1].get("url")

    # 3. Eksekusi FFmpeg dengan parameter sinkronisasi
    output_filename = "result.mp4"
    output_filepath = os.path.join(DOWNLOAD_FOLDER, output_filename)
    
    # Tambah -avoid_negative_ts make_zero untuk bantu sinkronisasi audio
    cmd = [
        "ffmpeg", "-y", "-ss", str(data.get('start_time')),
        "-i", stream_url, "-t", str(int(data.get('end_time')) - int(data.get('start_time'))),
        "-c:v", "libx264", "-c:a", "aac", "-preset", "veryfast",
        "-avoid_negative_ts", "make_zero", output_filepath
    ]
    
    subprocess.run(cmd)
    return jsonify({'download_url': f'/get-file/{output_filename}'})

# ... (tambahkan route @app.route('/') dan lainnya seperti kode lama kamu)
