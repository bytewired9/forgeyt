import os
import sys
import threading
import re
import subprocess
from yt_dlp import YoutubeDL, DownloadError

try:
    from vars import filetypes
    from utils.config import load_config
except ImportError:
    print("Error importing vars/config in dl.py. Using placeholders.")
    filetypes = {
        "mp3": {"filetype": "mp3", "fileext": "mp3", "audio": True, "codec": "mp3"},
        "mp4": {"filetype": "mp4", "fileext": "mp4", "audio": False, "codec": "libx264"}
    }
    def load_config():
        return {"download_path": os.path.expanduser("~")}

audio_bitrate_map = {
    "Best (≈192k)": '192',  # Maps the UI string to the bitrate value
    "High (128k)": '128',
    "Medium (96k)": '96',
    "Low (64k)": '64',
}

# --- Custom Exception for Cancellation ---
class DownloadCancelled(Exception):
    """Custom exception raised when download is cancelled via stop_event."""
    pass

# --- Helper to convert relative paths ---
def _convert_to_absolute(p):
    if p.startswith(("./", ".\\", "../", "..\\")):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.abspath(os.path.join(base_path, p))
    p = os.path.expanduser(p)
    return os.path.abspath(p)

# --- ANSI Stripping Regex ---
ANSI_ESCAPE_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences from a string."""
    if isinstance(text, str):
        return ANSI_ESCAPE_REGEX.sub('', text)
    return text

# --- Helper function to open file explorer ---
def open_file_explorer(path: str) -> None:
    """Opens the file explorer for the given path, reusing an existing window if available (Windows only)."""
    if os.name == "nt":
        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            folder_url = 'file:///' + os.path.abspath(path).replace('\\', '/')
            found = False
            for window in shell.Windows():
                try:
                    if window.LocationURL and window.LocationURL.lower() == folder_url.lower():
                        try:
                            window.Document.Focus()
                        except Exception:
                            pass
                        found = True
                        break
                except Exception:
                    continue
            if not found:
                os.startfile(path)
        except ImportError:
            os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])

def download(url: str, filetype_key: str, progress_callback: 'Signal',
             open_explorer_flag: bool, stop_event: threading.Event,
             # --- ALL Parameters with Defaults ---
             video_quality: str = 'Best',
             audio_quality: str = 'Best (≈192k)',
             embed_thumbnail: bool = False,
             playlist_range: str = '',
             playlist_reverse: bool = False,
             filename_template: str | None = None,
             keep_original: bool = False,
             embed_metadata: bool = False,
             embed_chapters: bool = False,
             write_infojson: bool = False,
             download_subtitles: bool = False,
             subtitle_langs: str = 'en',
             embed_subs: bool = False,
             autosubs: bool = False,
             rate_limit: str | None = None,
             cookie_file: str | None = None,
             sponsorblock_choice: str = 'None'
            ):
    """ Downloads video/audio using yt-dlp with extensive options. """
    final_filepath = None
    max_percentage_reported = 0.0

    def progress_hook(d):
        nonlocal final_filepath
        nonlocal max_percentage_reported

        if stop_event.is_set():
            raise DownloadCancelled("Download cancelled by user.")

        if d['status'] == 'downloading':
            percent_str = strip_ansi(d.get('_percent_str', '0.0%'))
            current_percentage_float = 0.0
            try:
                current_percentage_float = float(percent_str.strip().replace('%', ''))
            except ValueError:
                progress_callback.emit(f"\nWarning: Could not parse percentage: {percent_str}")
                current_percentage_float = max_percentage_reported

            percentage_to_display_float = max_percentage_reported
            if current_percentage_float >= max_percentage_reported:
                max_percentage_reported = current_percentage_float
                percentage_to_display_float = current_percentage_float
            else:
                delta = max_percentage_reported - current_percentage_float
                if current_percentage_float == 0.0 or delta > 20.0:
                    max_percentage_reported = current_percentage_float
                    percentage_to_display_float = current_percentage_float

            display_percentage_str = f"{percentage_to_display_float:.1f}%"
            total_bytes_str = strip_ansi(d.get('_total_bytes_str', 'N/A'))
            speed_str = strip_ansi(d.get('_speed_str', 'N/A'))
            eta_str = strip_ansi(d.get('_eta_str', 'N/A'))
            frag_info = ""
            if 'fragment_index' in d and 'fragment_count' in d:
                frag_info = f" (frag {d['fragment_index']}/{d['fragment_count']})"

            progress_line = f"\r[download] {display_percentage_str.strip():>6} of ~{total_bytes_str} at {speed_str} ETA {eta_str}{frag_info}"
            progress_callback.emit(progress_line)

        elif d['status'] == 'finished':
            final_filepath = d.get('filename') or d.get('info_dict', {}).get('_filename')
            final_max = max(max_percentage_reported, 100.0)
            final_progress_line = f"\r[download] {final_max:>6.1f}% of ~{strip_ansi(d.get('_total_bytes_str', 'N/A'))} completed."
            progress_callback.emit(final_progress_line)
            progress_callback.emit("")
            progress_callback.emit(strip_ansi(f"Download finished source: {os.path.basename(final_filepath or 'Unknown')}"))
            max_percentage_reported = 0.0

        elif d['status'] == 'error':
            progress_callback.emit("\nError during download hook.")
            max_percentage_reported = 0.0

    def postprocessor_hook(d):
        nonlocal final_filepath
        if stop_event.is_set():
            raise DownloadCancelled("Download cancelled during postprocessing.")
        if d['status'] in ('started', 'processing'):
            progress_callback.emit(strip_ansi(f"[PostProcessing] {d['postprocessor']} starting..."))
        elif d['status'] == 'finished':
            final_filepath = d.get('info_dict', {}).get('_filename')
            progress_callback.emit(strip_ansi(f"[PostProcessing] {d['postprocessor']} finished."))
        elif d['status'] == 'error':
            progress_callback.emit(strip_ansi(f"[PostProcessing] Error during {d.get('postprocessor', 'step')}"))

    try:
        progress_callback.emit(f"Preparing download for: {url}")
        config_data = load_config()
        download_path = _convert_to_absolute(config_data["download_path"])
        if not os.path.isdir(download_path):
            try:
                os.makedirs(download_path, exist_ok=True)
                progress_callback.emit(f"Created download directory: {download_path}")
            except OSError as e:
                raise OSError(f"Failed to create download directory '{download_path}': {e}")

        default_filetype_data = filetypes.get("mp3", {})
        format_info = filetypes.get(filetype_key, default_filetype_data)
        if not format_info:
            raise ValueError(f"Invalid file type key: '{filetype_key}'")
        fileext = format_info.get("fileext", "unknown")
        audio_only = format_info.get("audio", False)
        preferred_audio_quality = audio_bitrate_map.get(audio_quality, '192')

        progress_callback.emit(f"Selected format: {filetype_key.upper()} ({'Audio Only' if audio_only else 'Video'})")
        progress_callback.emit(f"Download path: {download_path}")
        if not audio_only:
            progress_callback.emit(f"Video Quality: {video_quality}")
        if audio_only:
            progress_callback.emit(f"Audio Quality: {audio_quality} (Target: {preferred_audio_quality}k)")
        if playlist_range:
            progress_callback.emit(f"Playlist Items: {playlist_range}")
        if playlist_reverse:
            progress_callback.emit("Playlist Order: Reversed")
        if filename_template:
            progress_callback.emit(f"Filename Template: {filename_template}")
        if keep_original:
            progress_callback.emit("Option: Keep Original Enabled")
        if embed_metadata:
            progress_callback.emit("Option: Embed Metadata Enabled")
        if embed_chapters:
            progress_callback.emit("Option: Embed Chapters Enabled")
        if write_infojson:
            progress_callback.emit("Option: Write info.json Enabled")
        if download_subtitles:
            progress_callback.emit(f"Option: Download Subs Enabled (Langs: {subtitle_langs})")
            if embed_subs:
                progress_callback.emit("Option: Embed Subs Enabled")
            if autosubs:
                progress_callback.emit("Option: Download Auto-Subs Enabled")
        if rate_limit:
            progress_callback.emit(f"Option: Rate Limit: {rate_limit}")
        if cookie_file:
            progress_callback.emit(f"Option: Using Cookie File: {os.path.basename(cookie_file)}")
        if sponsorblock_choice != 'None':
            progress_callback.emit(f"Option: SponsorBlock: {sponsorblock_choice}")

        ydl_opts = {
            "ignoreerrors": False,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
            "quiet": True,
            "no_mtime": True,
            "postprocessors": [],
            "outtmpl": os.path.join(download_path, '%(uploader)s - %(title)s.%(ext)s'),
            "playlistreverse": playlist_reverse,
            "playlist_items": playlist_range if playlist_range else None,
            "noplaylist": False,
            "keepvideo": keep_original,
            "embedmetadata": embed_metadata,
            "embedchapters": embed_chapters,
            "writethumbnail": embed_thumbnail,
            "writeinfojson": write_infojson,
            "writesubtitles": download_subtitles,
            "writeautomaticsub": download_subtitles and autosubs,
            "subtitleslangs": subtitle_langs.split(',') if download_subtitles else None,
            "subtitlesformat": "srt/best",
            "embedsubtitles": download_subtitles and embed_subs,
            "ratelimit": rate_limit,
            "cookiefile": cookie_file,
            "sponsorblock_remove": 'all' if sponsorblock_choice == 'Skip Sponsor Segments' else None,
            "sponsorblock_mark": 'all' if sponsorblock_choice == 'Mark Sponsor Segments' else None,
        }

        if filename_template:
            ydl_opts["outtmpl"] = os.path.join(download_path, filename_template)

        if embed_thumbnail:
            ydl_opts['postprocessors'].append({
                'key': 'EmbedThumbnail', 'already_have_thumbnail': False
            })

        if audio_only:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts['postprocessors'].append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": format_info.get("codec", fileext),  # Use expected audio codec
                "preferredquality": preferred_audio_quality,
            })
        else:
            quality_filter = ""
            if video_quality != "Best":
                height = "".join(filter(str.isdigit, video_quality))
                if height:
                    quality_filter = f"[height<=?{height}]"
            ydl_opts["format"] = (
                f"bestvideo{quality_filter}[ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo{quality_filter}+bestaudio/"
                f"best{quality_filter}"
            )
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoConvertor',
                'preferredformat': fileext,  # still use the container extension
                # Force the video codec conversion to the expected codec from the mapping
                'ffmpeg_args': ['-c:v', format_info.get("codec", "h264")]
            })


        ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None and v is not False and v != ''}
        if not ydl_opts.get('postprocessors'):
            if 'postprocessors' in ydl_opts:
                del ydl_opts['postprocessors']

        progress_callback.emit("Starting yt-dlp download process...")
        progress_callback.emit(f"Final Options: {ydl_opts}")

        with YoutubeDL(ydl_opts) as ydl:
            if stop_event.is_set():
                raise DownloadCancelled("Download cancelled before starting.")
            os.makedirs(download_path, exist_ok=True)
            ydl.download([url])

        if stop_event.is_set():
            progress_callback.emit("Download process stopped by user.")
            return None

        if final_filepath and os.path.exists(final_filepath):
            progress_callback.emit("Successfully downloaded and processed.")
            if open_explorer_flag:
                open_file_explorer(os.path.dirname(final_filepath))
            return final_filepath
        else:
            progress_callback.emit(f"Download/processing finished, but final file validation failed. Path: '{final_filepath}'")
            raise DownloadError("Download/processing finished, but the expected output file was not found or path is invalid.")

    except DownloadCancelled as e:
        progress_callback.emit(f"Operation Cancelled: {e}")
        raise
    except DownloadError as e:
        clean_error_msg = strip_ansi(str(e))
        progress_callback.emit(f"\nDownload Error: {clean_error_msg}")
        raise DownloadError(f"yt-dlp error: {clean_error_msg}") from e
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        clean_error_msg = strip_ansi(str(e))
        progress_callback.emit(f"\nUnexpected Error: {clean_error_msg}\n{err_trace}")
        raise Exception(f"An unexpected error occurred: {clean_error_msg}") from e
