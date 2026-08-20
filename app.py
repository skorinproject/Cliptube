cat << 'EOF' > app.py
import os
import subprocess
from flask import Flask, render_template, request, send_file

app = Flask(__name__)
# Kita simpan sementara di folder aplikasi, nanti browser yang narik
TEMP_FOLDER = 'temp_clips'
os.makedirs(TEMP_FOLDER, exist_ok=True)

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
    
    filename = f"clip_{start_sec}_{end_sec}.mp4"
    filepath = os.path.join(TEMP_FOLDER, filename)

    if res == '360': fmt = "18/best[height<=360]"
    elif res == '720': fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    else: fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"

    cmd = [
        "yt-dlp", "-f", fmt, "--extractor-args", "youtube:player_client=mweb",
        "--download-sections", f"*{start_sec}-{end_sec}",
        "--merge-output-format", "mp4", "-o", filepath, url
    ]

    try:
        subprocess.run(cmd, check=True)
        # Kirim file ke browser, browser akan otomatis download
        return send_file(filepath, as_attachment=True, download_name=filename)
    except:
        return "Error saat memotong video", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
