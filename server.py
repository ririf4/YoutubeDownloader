import traceback
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL

from downloader import YouTubeDownloader
import subprocess
app = FastAPI(
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"]
        )
    ]
)
yt_downloader = YouTubeDownloader()

class DownloadRequest(BaseModel):
    url: str
    type: str
    format: str
    resolution: str | None = None
    video_bitrate: str | None = None
    audio_bitrate: str | None = None
    output_dir: str = "./downloads"

class OptionsRequest(BaseModel):
    url: str

def extract_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def get_ffmpeg_formats():
    try:
        result = subprocess.run(["bin/ffmpeg.exe", "-hide_banner", "-formats"],
                                capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        formats = []
        for line in lines:
            if line.startswith(" DE") or line.startswith(" D "):
                parts = line.split()
                if len(parts) >= 2:
                    formats.append(parts[1])
        return sorted(set(formats))
    except Exception:
        return ["mp4", "mp3", "wav", "ogg"]


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    video_id = query.get("v", [""])[0]
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

@app.post("/options")
async def get_options(req: OptionsRequest):
    try:
        print(">>> URL:", req.url)
        url = clean_url(req.url)
        print(">>> Clean URL:", url)
        info = extract_info(url)
        print(">>> Info: ", info)

        video_streams = [f for f in info["formats"] if f.get("vcodec") != "none" and f.get("acodec") != "none"]
        audio_streams = [f for f in info["formats"] if f.get("vcodec") == "none"]

        resolutions = sorted(
            {f"{f['height']}p" for f in video_streams if f.get("height")},
            key=lambda r: int(r.replace("p", "")), reverse=True
        )

        audio_bitrates = sorted(
            {f"{int(f['abr'])}k" for f in audio_streams if f.get("abr")},
            key=lambda b: int(b.replace("k", "")), reverse=True
        )

        ffmpeg_formats = get_ffmpeg_formats()
        audio_formats = [f for f in ffmpeg_formats if f in ["mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"]]
        video_formats = [f for f in ffmpeg_formats if f in ["mp4", "mkv", "avi", "webm", "mov"]]

        return {
            "video": {
                "resolutions": resolutions,
                "audio_bitrates": audio_bitrates,
                "formats": video_formats
            },
            "audio": {
                "bitrates": audio_bitrates,
                "formats": audio_formats
            }
        }

    except Exception as e:
        print("[/options ERROR]")
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/download")
async def download(req: DownloadRequest):
    try:
        if req.type == "audio":
            path = yt_downloader.download_audio(
                url=req.url,
                file_format=req.format,
                bitrate=req.audio_bitrate or "128k",
                output_dir=req.output_dir
            )
        else:
            path = yt_downloader.download_video(
                url=req.url,
                resolution=req.resolution or "720p",
                file_format=req.format,
                audio_bitrate=req.video_bitrate or "128k",
                output_dir=req.output_dir
            )
        return {"status": "success", "file": path}
    except Exception as e:
        return {"status": "error", "message": str(e)}