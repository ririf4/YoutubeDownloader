import datetime
from pathlib import Path

from yt_dlp import YoutubeDL

from main import get_ffmpeg_dir


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

    def download_audio(self, url: str, file_format: str, bitrate: str, output_dir: str, output_format: str) -> str:
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
            'ffmpeg_location': str(get_ffmpeg_dir())
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            output_path = Path(ydl.prepare_filename(info))

            final_ext = output_format or file_format
            final_path = output_path.with_suffix(f".{final_ext}")

            if final_path.exists():
                return str(final_path)
            elif output_path.exists():
                return str(output_path)
            else:
                raise FileNotFoundError(f"Could not locate downloaded file: {output_path.name}")

    def download_video(
            self,
            url: str,
            resolution: str,
            file_format: str,
            audio_bitrate: str,
            output_dir: str,
            output_format: str | None = None,
            audio_format: str | None = None
    ) -> str:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        supports_thumbnail = (output_format or file_format).lower() in ("mp4", "mkv")

        resolution_number = resolution.replace("p", "")

        post_args = [
            '-b:a', audio_bitrate,
            '-metadata', 'title=Downloaded by YouTubeDownloader',
            '-metadata', 'artist=RiriFa Studio 🎧'
        ]

        audio_encoder_map = {
            "m4a": "aac",
            "mp4": "aac",
            "mp3": "libmp3lame",
            "webm": "libopus",
            "ogg": "libvorbis"
        }
        encoder = audio_encoder_map.get(audio_format.lower(), audio_format)

        if audio_format:
            post_args.extend(['-c:a', encoder])

        ydl_opts = {
            'format': f"bestvideo[height={resolution_number}][ext={file_format}]+bestaudio",
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'merge_output_format': output_format or file_format,
            'postprocessor_args': post_args,
            'quiet': False,
            'ffmpeg_location': str(get_ffmpeg_dir())
        }

        if supports_thumbnail:
            ydl_opts['writethumbnail'] = True
            ydl_opts.setdefault('postprocessors', [])
            ydl_opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            })

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            output_path = Path(ydl.prepare_filename(info))

            final_ext = output_format or file_format
            final_path = output_path.with_suffix(f".{final_ext}")

            if final_path.exists():
                return str(final_path)
            elif output_path.exists():
                return str(output_path)
            else:
                raise FileNotFoundError(f"Could not locate downloaded file: {output_path.name}")
