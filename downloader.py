import os
import datetime
from pathlib import Path
from yt_dlp import YoutubeDL

from main import get_ffmpeg_path


# noinspection DuplicatedCode
class YouTubeDownloader:
    def __init__(self):
        pass

    def _get_unique_filename(self, path: str, title: str, ext: str) -> str:
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-")
        base = Path(path) / f"{safe_title}{ext}"
        if not base.exists():
            return str(base)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return str(Path(path) / f"{safe_title}_{timestamp}{ext}")

    def download_audio(self, url: str, file_format: str, bitrate: str, output_dir: str) -> str:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': file_format,
                'preferredquality': bitrate.replace("k", ""),
            }],
            'quiet': False,
            'ffmpeg_location': str(get_ffmpeg_path())
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = self._get_unique_filename(str(output_dir), info['title'], f'.{file_format}')
            if Path(filename).exists():
                return filename
            else:
                # fallback to whatever yt-dlp created
                return str(list(output_dir.glob(f"{info['title']}*.{file_format}"))[0])

    def download_video(self, url: str, resolution: str, file_format: str, audio_bitrate: str, output_dir: str) -> str:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        supports_thumbnail = file_format.lower() in ("mp4", "mkv")

        ydl_opts = {
            'format': f'bestvideo[height={resolution[:-1]}]+bestaudio/best',
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'merge_output_format': file_format,
            'postprocessor_args': [
                '-b:a', audio_bitrate,
                '-metadata', 'title=Downloaded by YouTubeDownloader',
                '-metadata', 'artist=RiriFa Studio 🎧'
            ],
            'quiet': False,
            'ffmpeg_location': str(get_ffmpeg_path())
        }

        if supports_thumbnail:
            ydl_opts['writethumbnail'] = True
            ydl_opts.setdefault('postprocessors', [])
            ydl_opts['postprocessors'].extend([
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'}
            ])

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = self._get_unique_filename(str(output_dir), info['title'], f'.{file_format}')
            if Path(filename).exists():
                return filename
            else:
                return str(list(output_dir.glob(f"{info['title']}*.{file_format}"))[0])
