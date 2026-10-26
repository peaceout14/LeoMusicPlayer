# LeoMusicPlayer

**Course:** Web Technology (NBTCE503T)  
**Student Name:** Mahir Dipakbhai Patel  
**IAR Registration No.:** 15846  
**Program:** B.Tech IT (Semester V)  

---

## Project Overview

**LeoMusicPlayer** is a full-stack, responsive web application designed for online music discovery, queue management, and real-time audio streaming. 

The application features a modern glassmorphism UI built with plain HTML5, CSS3, and modern JavaScript, coupled with a Python FastAPI backend. It utilizes the YouTube Data API v3 for search indexing, `yt-dlp` and `FFmpeg` for on-demand audio extraction/conversion, SQLite for metadata caching, and HTTP 206 Byte-Range streaming for fast, buffer-free playback.

---

## Features

- **YouTube Track Search:** Real-time search powered by YouTube Data API v3.
- **Audio Conversion & Cache:** Automatic extraction and conversion to 192kbps MP3 format with SQLite metadata caching to avoid repeated downloads.
- **HTTP 206 Range Streaming:** Efficient binary streaming supporting rapid seeking and buffering.
- **Interactive Player UI:**
  - Play / Pause / Seek bar controls with smooth track timeline scrubbing.
  - Custom Volume slider.
  - Track Looping and automatic Queue playback.
  - Dynamic thumbnail generation from YouTube video IDs.
- **Queue System:** Add tracks to an "Up Next" queue, play items on-demand, or remove items individually.

---

## Tech Stack

- **Frontend:** HTML5, CSS3 (Glassmorphism design), ES6+ JavaScript (Fetch API)
- **Backend:** Python 3.10+, FastAPI, Uvicorn (ASGI Server)
- **Database:** SQLite3
- **Media Engine:** `yt-dlp` (with EJS support), FFmpeg
- **External API:** YouTube Data API v3

---

## Prerequisites & Dependencies

Before running the application, ensure the following tools are installed on your system:

1. **Python 3.10 or higher**
2. **Node.js (v18+)** — *Required by `yt-dlp` for solving YouTube JavaScript signature challenges.*
3. **FFmpeg** — *Required for audio conversion to MP3 format.*

### Installing FFmpeg

- **Windows (Command Prompt):**
  ```cmd
  winget install Gyan.FFmpeg
  ```
- **macOS (Homebrew):**
  ```bash
  brew install ffmpeg
  ```

---

## Installation & Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/peaceout14/LeoMusicPlayer.git
cd LeoMusicPlayer
```

### 2. Install Python Packages
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your YouTube Data API Key:
```env
YOUTUBE_API_KEY=your_google_youtube_api_key_here
```

### 4. Run the Backend Server
Start the FastAPI server using Uvicorn:
```bash
python -m uvicorn song:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the Web Player
Open your web browser and navigate to:
```text
http://localhost:8000
```
*(Alternatively, open `index.html` directly in your browser or access it via local IP on your network)*

---

## Project Structure

```text
LeoMusicPlayer/
│
├── song.py               # FastAPI backend server & audio handling
├── index.html            # Web audio player frontend UI
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
├── .gitignore            # Git exclusion rules
├── .env                  # Environment secrets (API Keys)
├── downloads/            # Local directory for downloaded MP3 files (Auto-generated)
└── music_library.db      # SQLite database for track caching (Auto-generated)
```

---

## Academic Evaluation Checklist

- [x] Functional HTML5/CSS3/JS Audio Player
- [x] Backend FastAPI Server with Async Endpoints
- [x] SQLite Database Caching
- [x] Real-time Track Search & Audio Streaming
- [x] Queue & Track Control System
