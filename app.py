from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading
import time

FFMPEG_PATH = r"C:\Users\annie\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

progress_store = {}

def clean_old_files():
    while True:
        now = time.time()
        for fname in os.listdir(DOWNLOAD_FOLDER):
            fpath = os.path.join(DOWNLOAD_FOLDER, fname)
            if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > 600:
                os.remove(fpath)
        time.sleep(60)

threading.Thread(target=clean_old_files, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Please enter a URL"}), 400

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        seen = set()

        for f in info.get("formats", []):
            height = f.get("height")
            vcodec = f.get("vcodec", "none")

            if vcodec != "none" and height:
                label = f"{height}p MP4"
                if label not in seen:
                    seen.add(label)
                    formats.append({
                        "format_id": f["format_id"],
                        "label": label,
                        "type": "video",
                        "height": height
                    })

        formats.append({
            "format_id": "bestaudio/best",
            "label": "Best Audio (MP3)",
            "type": "audio",
            "height": 0
        })

        formats = sorted(formats, key=lambda x: x["height"], reverse=True)

        final_formats = []
        seen_labels = set()
        for f in formats:
            if f["label"] not in seen_labels:
                seen_labels.add(f["label"])
                final_formats.append(f)

        return jsonify({
            "title": info.get("title", "Unknown Title"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
            "formats": final_formats
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url", "").strip()
    format_id = data.get("format_id", "bestvideo+bestaudio/best")
    is_audio = data.get("is_audio", False)
    job_id = str(uuid.uuid4())

    progress_store[job_id] = {"status": "starting", "percent": 0}

    def progress_hook(d):
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                progress_store[job_id]["percent"] = float(pct)
                progress_store[job_id]["status"] = "downloading"
            except:
                pass
        elif d["status"] == "finished":
            progress_store[job_id]["status"] = "processing"
            progress_store[job_id]["percent"] = 99

    output_path = os.path.join(DOWNLOAD_FOLDER, f"{job_id}")

    if is_audio:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path + ".%(ext)s",
            "quiet": True,
            "progress_hooks": [progress_hook],
            "ffmpeg_location": FFMPEG_PATH,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        ydl_opts = {
            "format": f"bestvideo[vcodec^=avc]+bestaudio/bestvideo+bestaudio/best",
            "outtmpl": output_path + ".%(ext)s",
            "quiet": True,
            "progress_hooks": [progress_hook],
            "ffmpeg_location": FFMPEG_PATH,
            "merge_output_format": "mp4",
            # Convert audio to AAC so it works on all players
            "postprocessor_args": {
                "ffmpeg": ["-c:a", "aac"]
            },
        }

    def do_download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "video")
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.startswith(job_id):
                    progress_store[job_id]["status"] = "done"
                    progress_store[job_id]["percent"] = 100
                    progress_store[job_id]["filename"] = f
                    progress_store[job_id]["title"] = title
                    break
        except Exception as e:
            progress_store[job_id]["status"] = "error"
            progress_store[job_id]["error"] = str(e)

    t = threading.Thread(target=do_download)
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/progress/<job_id>")
def progress(job_id):
    info = progress_store.get(job_id, {"status": "not_found"})
    return jsonify(info)


@app.route("/file/<job_id>")
def get_file(job_id):
    info = progress_store.get(job_id, {})
    filename = info.get("filename")
    title = info.get("title", "download")

    if not filename:
        return jsonify({"error": "File not ready"}), 404

    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    ext = filename.rsplit(".", 1)[-1]
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:60]
    download_name = f"{safe_title}.{ext}"

    return send_file(filepath, as_attachment=True, download_name=download_name)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
