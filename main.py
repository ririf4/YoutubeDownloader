import sys

import webview
import threading
import os
import zipfile
import urllib.request
from pathlib import Path
from pydub import AudioSegment
import tkinter as tk
from tkinter import filedialog
import uvicorn

import server

BIN_DIR = Path("bin")
FFMPEG_EXE = BIN_DIR / "ffmpeg.exe"

class Api:
    def select_folder(self):
        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory()
        return folder or ""

def get_ffmpeg_path():
    appdata = Path(os.getenv("LOCALAPPDATA") or Path.home())
    ffmpeg_dir = appdata / "YouTubeDownloader" / "ffmpeg"
    ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
    return ffmpeg_exe

def ensure_ffmpeg():
    ffmpeg_exe = get_ffmpeg_path()
    if ffmpeg_exe.exists():
        AudioSegment.converter = str(ffmpeg_exe)
        print(f"[INFO] Using FFmpeg from: {ffmpeg_exe}")
        return

    print("[INFO] FFmpeg not found. Downloading to AppData...")

    ffmpeg_dir = ffmpeg_exe.parent
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)

    zip_path = ffmpeg_dir / "ffmpeg.zip"
    FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    urllib.request.urlretrieve(FFMPEG_URL, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(ffmpeg_dir)

    for root, _, files in os.walk(ffmpeg_dir):
        if "ffmpeg.exe" in files:
            Path(root, "ffmpeg.exe").rename(ffmpeg_exe)
            break

    zip_path.unlink()
    AudioSegment.converter = str(ffmpeg_exe)
    print(f"[INFO] FFmpeg is ready in: {ffmpeg_exe}")

def start_fastapi():
    uvicorn.run(server.app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    ensure_ffmpeg()

    api = Api()

    threading.Thread(target=start_fastapi, daemon=True).start()

    webview.create_window("YouTube Downloader", "frontend/index.html", js_api=api, width=800, height=700)
    webview.start(debug=True)
