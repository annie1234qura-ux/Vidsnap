# VidSnap – Video Downloader Web App

Download videos from YouTube, Instagram, TikTok, Twitter/X, Facebook, and 1000+ other sites.

## Requirements

- Python 3.8 or higher
- pip
- ffmpeg (for merging video + audio)

## Setup Instructions

### Step 1 – Install FFmpeg

**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to PATH, OR place ffmpeg.exe in the project folder

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

---

### Step 2 – Install Python packages

Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

---

### Step 3 – Run the app

```bash
python app.py
```

Then open your browser and go to:

```
http://localhost:5000
```

---

## How to Use

1. Paste a video URL (YouTube, Instagram, TikTok, etc.)
2. Click **Get Video**
3. Choose your quality and format (MP4 or MP3)
4. Click **Download**
5. The file saves to your Downloads folder automatically

---

## Supported Sites

- YouTube
- Instagram (Reels, posts)
- TikTok
- Twitter / X
- Facebook
- Vimeo
- Reddit
- 1000+ more via yt-dlp

---

## Notes

- Downloaded files are auto-deleted from the server after 10 minutes
- For personal use only — respect copyright laws
- Some platforms may require login for private content
