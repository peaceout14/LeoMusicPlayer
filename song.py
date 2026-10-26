from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import sqlite3
import yt_dlp
import os
import re
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
DB_PATH      = "music_library.db"
#BASE_URL     = "http://localhost:8000"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL,
            title    TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', "_", name.strip())
    name = re.sub(r'[^\w\-.]', "", name)
    return name[:200]


def get_song_from_db(video_id: str):
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM songs WHERE video_id = ?", (video_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def save_song_to_db(video_id: str, title: str, file_path: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO songs (video_id, title, file_path) VALUES (?, ?, ?)",
        (video_id, title, file_path),
    )
    conn.commit()
    conn.close()


@app.get("/search")
async def search_songs(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": []}
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "maxResults": 5, "q": q,
                    "type": "video", "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        results = []
        for item in resp.json().get("items", []):
            title    = item.get("snippet", {}).get("title", "")
            title    = title.replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
            video_id = item.get("id", {}).get("videoId", "")
            if title and video_id:
                results.append({"title": title, "id": video_id})
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-song")
async def get_song(request: Request, video_id: str, title: str): # <-- Added request: Request
    # Dynamically get the base URL (e.g., http://192.168.29.157:8000)
    base_url = str(request.base_url).rstrip("/")

    # 1. Serve from cache if already downloaded
    cached = get_song_from_db(video_id)
    if cached and os.path.exists(cached):
        filename = os.path.basename(cached)
        return {"file_url": f"{base_url}/stream?filename={requests.utils.quote(filename)}", "title": title}

    # 2. Download via yt-dlp
    safe_title      = sanitize_filename(title)
    output_template = os.path.join(DOWNLOAD_DIR, f"{safe_title}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet":   True,
        "nocheckcertificate": True,
        "remote_components": ["ejs:github"],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "web_embedded"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    # 3. Find downloaded file
    downloaded_file = None
    for f in sorted(os.listdir(DOWNLOAD_DIR)):
        if f.startswith(safe_title) and not f.endswith(".part") and not f.endswith(".ytdl"):
            downloaded_file = os.path.join(DOWNLOAD_DIR, f)
            break

    if not downloaded_file:
        raise HTTPException(status_code=500, detail="File not found after download.")

    save_song_to_db(video_id, title, downloaded_file)
    filename = os.path.basename(downloaded_file)
    
    # Return the dynamic URL
    return {"file_url": f"{base_url}/stream?filename={requests.utils.quote(filename)}", "title": title}


@app.get("/stream")
async def stream_audio(request: Request, filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    abs_path = os.path.realpath(file_path)
    if not abs_path.startswith(os.path.realpath(DOWNLOAD_DIR)):
        raise HTTPException(status_code=403, detail="Forbidden")

    file_size  = os.path.getsize(file_path)
    ext        = os.path.splitext(filename)[1].lower()
    mime_map   = {".webm": "audio/webm", ".m4a": "audio/mp4",
                  ".mp4": "audio/mp4", ".mp3": "audio/mpeg",
                  ".opus": "audio/ogg; codecs=opus", ".ogg": "audio/ogg"}
    media_type = mime_map.get(ext, "application/octet-stream")
    chunk_size = 512 * 1024

    range_header = request.headers.get("range")
    if range_header:
        parts  = range_header.replace("bytes=", "").split("-")
        start  = int(parts[0]) if parts[0] else 0
        end    = int(parts[1]) if parts[1] else file_size - 1
        end    = min(end, file_size - 1)
        length = end - start + 1

        def iter_range():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(iter_range(), status_code=206, media_type=media_type,
                                 headers={"Content-Range": f"bytes {start}-{end}/{file_size}",
                                          "Accept-Ranges": "bytes",
                                          "Content-Length": str(length)})

    def iter_full():
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    return StreamingResponse(iter_full(), status_code=200, media_type=media_type,
                             headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)})



@app.get("/debug")
async def debug_download(video_id: str, title: str):
    """Test endpoint — shows exactly what yt-dlp does without playing."""
    import traceback
    safe_title      = sanitize_filename(title)
    output_template = os.path.join(DOWNLOAD_DIR, f"{safe_title}.%(ext)s")
    youtube_url     = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
        "outtmpl": output_template,
        "quiet":   True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
        return {"status": "ok", "title": info.get("title"), "formats": len(info.get("formats", []))}
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

# Serve images and other static files
app.mount("/", StaticFiles(directory=".", html=True), name="static")
