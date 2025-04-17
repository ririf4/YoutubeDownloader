import subprocess
import traceback
from typing import List
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware import Middleware
from yt_dlp import YoutubeDL

from downloader import YouTubeDownloader

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
    type: str                     # "video" or "audio"
    format: str                   # 最終出力形式（例: mp4）
    resolution: str | None = None
    resolution_format: str | None = None
    audio_bitrate: str | None = None
    audio_format: str | None = None
    output_dir: str = "./downloads"


class ResolutionOption(BaseModel):
    resolution: str
    source_formats: List[str]
class BitrateOption(BaseModel):
    bitrate: str
    source_formats: List[str]
class VideoOptions(BaseModel):
    resolutions: List[ResolutionOption]
    audio_bitrates: List[BitrateOption]
    formats: List[str]
class AudioOptions(BaseModel):
    bitrates: List[BitrateOption]
    formats: List[str]
class OptionsResponse(BaseModel):
    title: str
    channel: str
    upload_date: str
    duration: int
    video: VideoOptions
    audio: AudioOptions
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
        print(">>> Info:", info)

        formats = info["formats"]

        # ───── VIDEO STREAMS ─────
        video_streams = [
            f for f in formats
            if f.get("vcodec") != "none" and f.get("height")
        ]

        # {解像度: [使用されている拡張子]}
        video_resolution_map = {}
        for f in video_streams:
            height = f.get("height")
            ext = f.get("ext")
            res = f"{height}p"
            video_resolution_map.setdefault(res, set()).add(ext)

        # ───── AUDIO STREAMS ─────
        audio_streams = [
            f for f in formats if f.get("vcodec") == "none" and f.get("abr")
        ]

        # {bitrate: [使用されている拡張子]}
        audio_bitrate_map = {}
        for f in audio_streams:
            bitrate = f"{int(f.get('abr'))}k"
            ext = f.get("ext")
            audio_bitrate_map.setdefault(bitrate, set()).add(ext)

        # ───── フォーマット一覧（FFmpeg）─────
        ffmpeg_formats = get_ffmpeg_formats()
        audio_formats = [f for f in ffmpeg_formats if f in ["mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"]]
        video_formats = [f for f in ffmpeg_formats if f in ["mp4", "mkv", "avi", "webm", "mov"]]

        # ───── 構造を整形して返す ─────
        return OptionsResponse(
            title=info.get("title", "Unknown"),
            channel=info.get("uploader", "Unknown"),
            upload_date=info.get("upload_date", "")[:4] + "-" + info.get("upload_date", "")[4:6] + "-" + info.get("upload_date", "")[6:],
            duration=info.get("duration", 0),
            video=VideoOptions(
                resolutions=[
                    ResolutionOption(
                        resolution=res,
                        source_formats=list(exts)
                    ) for res, exts in sorted(
                        video_resolution_map.items(),
                        key=lambda x: int(x[0].replace("p", "")),
                        reverse=True
                    )
                ],
                audio_bitrates=[
                    BitrateOption(
                        bitrate=bitrate,
                        source_formats=list(exts)
                    ) for bitrate, exts in sorted(
                        audio_bitrate_map.items(),
                        key=lambda x: int(x[0].replace("k", "")),
                        reverse=True
                    )
                ],
                formats=video_formats
            ),
            audio=AudioOptions(
                bitrates=[
                    BitrateOption(
                        bitrate=bitrate,
                        source_formats=list(exts)
                    ) for bitrate, exts in sorted(
                        audio_bitrate_map.items(),
                        key=lambda x: int(x[0].replace("k", "")),
                        reverse=True
                    )
                ],
                formats=audio_formats
            )
        )

    except Exception as e:
        print("[/options ERROR]")
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/download")
async def download(req: DownloadRequest):
    try:
        print("[/download] Received payload:", req.model_dump())

        resolution = req.resolution or "720p"
        resolution_format = req.resolution_format or req.format
        audio_bitrate = req.audio_bitrate or "128k"
        audio_format = req.audio_format or req.format
        output_format = req.format

        if req.type == "audio":
            path = yt_downloader.download_audio(
                url=req.url,
                file_format=output_format,
                bitrate=audio_bitrate,
                output_dir=req.output_dir,
                output_format=output_format
            )
        elif req.type == "video":
            path = yt_downloader.download_video(
                url=req.url,
                resolution=resolution,
                file_format=resolution_format,
                audio_bitrate=audio_bitrate,
                output_dir=req.output_dir,
                output_format=output_format,
                audio_format=audio_format
            )
        else:
            return {"status": "error", "message": f"Invalid type: {req.type}"}

        return {"status": "success", "file": path}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
