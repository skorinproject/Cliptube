@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    start = data.get('start')
    end = data.get('end')
    res = data.get('resolution', '720')

    start_sec = to_seconds(start)
    end_sec = to_seconds(end)

    resolutions = {
        '360': '640:360',
        '480': '854:480',
        '720': '1280:720',
        '1080': '1920:1080'
    }

    if res not in resolutions:
        return jsonify({
            "status": "error",
            "message": "Resolusi tidak valid"
        }), 400

    width_height = resolutions[res]

    filename = f"clip_{res}p_{start_sec}_{end_sec}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    # File sementara
    temp_file = os.path.join(
        DOWNLOAD_FOLDER,
        f"temp_{start_sec}_{end_sec}.mp4"
    )

    try:
        # 1. Download video terbaik yang tersedia
        cmd_download = [
            "yt-dlp",
            "-f", "bv*+ba/b",
            "--download-sections", f"*{start_sec}-{end_sec}",
            "--merge-output-format", "mp4",
            "-o", temp_file,
            url
        ]

        subprocess.run(cmd_download, check=True)

        # 2. Paksa resolusi menggunakan FFmpeg
        cmd_ffmpeg = [
            "ffmpeg",
            "-y",
            "-i", temp_file,
            "-vf", f"scale={width_height}:force_original_aspect_ratio=decrease,"
                    f"pad={width_height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            filepath
        ]

        subprocess.run(cmd_ffmpeg, check=True)

        # Hapus file sementara
        if os.path.exists(temp_file):
            os.remove(temp_file)

        # Refresh media scanner Android
        subprocess.run([
            "am",
            "broadcast",
            "-a",
            "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d",
            f"file://{filepath}"
        ])

        return jsonify({
            "status": "sukses",
            "message": f"Berhasil dibuat dalam resolusi {res}p",
            "filename": filename
        })

    except Exception as e:

        if os.path.exists(temp_file):
            os.remove(temp_file)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
