# app/workers.py
import os
import json
import re # Import regex for parsing progress
import threading # Import threading
import traceback # For detailed error logging
import requests # For UpdateCheckWorker

from PySide6.QtCore import QObject, Signal, Slot, QThread

# --- Utility Imports with Fallbacks ---
try:
    from utils.dl import download as download, DownloadCancelled
except ImportError as e:
    print(f"ERROR in workers.py: Failed importing 'utils.dl': {e}. Using placeholder.")
    def placeholder_download_fallback(url, filetype_key, progress_callback, open_explorer_flag, stop_event):
        progress_callback.emit(f"PLACEHOLDER: Simulating download for {url} as {filetype_key}")
        import time
        for i in range(101):
            if stop_event.is_set():
                progress_callback.emit("PLACEHOLDER: Cancelled.")
                return None # Indicate cancellation
            progress_callback.emit(f"\r[download] {i}% of 10MiB")
            time.sleep(0.02)
        progress_callback.emit("\nPLACEHOLDER: Done.")
        return os.path.join(os.path.expanduser("~"), f"placeholder_{filetype_key}.file")
    download = placeholder_download_fallback

    class DownloadCancelled(Exception):
        pass

try:
    from utils import CURRENT_VERSION
except ImportError:
    print("ERROR in workers.py: Failed importing 'CURRENT_VERSION' from utils. Using placeholder.")
    CURRENT_VERSION = "0.0.0-fallback"
# --- End Fallbacks ---


# --- Worker Thread Objects ---


class DownloadWorker(QObject):
    """ Worker object to handle downloads using download with many options. """
    download_complete = Signal(bool, str)
    progress_update = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, filetype: str, open_explorer_var: bool,
                 # Basic Quality/Format
                 video_quality: str, audio_quality: str,
                 # *** ADDED: Codec parameters ***
                 video_codec: str | None, audio_codec: str | None,
                 # *** END ADDED ***
                 embed_thumbnail: bool,
                 # Playlist
                 playlist_range: str, playlist_reverse: bool,
                 # Output
                 filename_template: str | None, keep_original: bool,
                 # Metadata
                 embed_metadata: bool, embed_chapters: bool, write_infojson: bool,
                 # Subtitles
                 download_subtitles: bool, subtitle_langs: str, embed_subs: bool, autosubs: bool,
                 # Network
                 rate_limit: str | None, cookie_file: str | None,
                 # YouTube
                 sponsorblock_choice: str,
                 parent: QObject | None = None):
        super().__init__(parent)
        # Store all parameters
        self.url = url
        self.filetype = filetype
        self.open_explorer_var = open_explorer_var
        self.video_quality = video_quality
        self.audio_quality = audio_quality
        # *** ADDED: Store codecs ***
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        # *** END ADDED ***
        self.embed_thumbnail = embed_thumbnail
        self.playlist_range = playlist_range
        self.playlist_reverse = playlist_reverse
        self.filename_template = filename_template
        self.keep_original = keep_original
        self.embed_metadata = embed_metadata
        self.embed_chapters = embed_chapters
        self.write_infojson = write_infojson
        self.download_subtitles = download_subtitles
        self.subtitle_langs = subtitle_langs
        self.embed_subs = embed_subs
        self.autosubs = autosubs
        self.rate_limit = rate_limit
        self.cookie_file = cookie_file
        self.sponsorblock_choice = sponsorblock_choice
        # --- Stop Event (Existing) ---
        self.stop_event = threading.Event()

    @Slot()
    def run(self):
        """ Executes the actual download function with all options. """
        final_path = None
        try:
            # *** PASS ALL OPTIONS TO download ***
            final_path = download(
                url=self.url,
                filetype_key=self.filetype,
                progress_callback=self.progress_update,
                open_explorer_flag=self.open_explorer_var, # Passed but not used by dl.py
                stop_event=self.stop_event,
                # Pass all stored options
                video_quality=self.video_quality,
                audio_quality=self.audio_quality,
                # *** ADDED: Pass stored codecs ***
                video_codec=self.video_codec,
                audio_codec=self.audio_codec,
                # *** END ADDED ***
                embed_thumbnail=self.embed_thumbnail,
                playlist_range=self.playlist_range,
                playlist_reverse=self.playlist_reverse,
                filename_template=self.filename_template,
                keep_original=self.keep_original,
                embed_metadata=self.embed_metadata,
                embed_chapters=self.embed_chapters,
                write_infojson=self.write_infojson,
                download_subtitles=self.download_subtitles,
                subtitle_langs=self.subtitle_langs,
                embed_subs=self.embed_subs,
                autosubs=self.autosubs,
                rate_limit=self.rate_limit,
                cookie_file=self.cookie_file,
                sponsorblock_choice=self.sponsorblock_choice
            )
            # --- Result Handling (Existing - slightly refined) ---
            if final_path and not self.stop_event.is_set():
                self.download_complete.emit(True, final_path)
            elif self.stop_event.is_set():
                self.download_complete.emit(False, "Download cancelled by user.")
            else: # Download finished but no path returned or validation failed in dl.py
                  # Error should have been emitted by dl.py via progress_callback or raised
                  # If dl.py returned None without raising/cancelling, treat as failure.
                  # Emit error signal if not already emitted by dl.py via progress_callback
                  # Check if an error signal was already emitted maybe? Or just emit completion=False
                  # self.error.emit("Download failed: No valid file path received.") # Potentially duplicate
                  self.download_complete.emit(False, "Download failed or file path missing.")

        except DownloadCancelled as e:
            print(f"Download worker caught cancellation: {e}")
            self.download_complete.emit(False, str(e)) # Emit completion=False with reason

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"Error in download worker thread: {traceback.format_exc()}")
            self.error.emit(error_msg) # Emit specific error
            # Emit completion=False as well, perhaps with a generic message
            # self.download_complete.emit(False, "Download failed due to an unexpected error.") # Maybe redundant if error is emitted

    def request_stop(self):
        """ Signals the download logic to stop. """
        self.stop_event.set()

class UpdateCheckWorker(QObject):
    """ Worker object to check for updates asynchronously. """
    update_available = Signal(str) # Emits latest version string if newer
    check_finished = Signal()      # Emits when done, regardless of result
    check_error = Signal(str)      # Emits on error

    @Slot()
    def run(self):
        """ Performs the network request and version comparison. """
        try:
            latest_version = self._get_latest_release_sync()
            if latest_version and self._is_newer_version_sync(CURRENT_VERSION, latest_version):
                self.update_available.emit(latest_version)
        except Exception as e:
            self.check_error.emit(f"Update check failed: {e}")
        finally:
            self.check_finished.emit()

    def _get_latest_release_sync(self) -> str | None:
        """ Fetches the latest release tag name from GitHub API. """
        url = "https://api.github.com/repos/bytewired9/forgeyt/releases/latest"
        headers = {'Accept': 'application/vnd.github.v3+json', 'X-GitHub-Api-Version': '2022-11-28'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            tag_name = data.get('tag_name')
            if tag_name and isinstance(tag_name, str) and '.' in tag_name:
                return tag_name.lstrip('v')
            else:
                print(f"Warning: Unexpected tag_name format received: {tag_name}")
                return None
        except requests.exceptions.Timeout:
            print("Update check failed: Request timed out.")
            raise TimeoutError("GitHub API request timed out.")
        except requests.exceptions.RequestException as e:
            print(f"Update check failed: Network error - {e}")
            raise ConnectionError(f"Network error during update check: {e}")
        except json.JSONDecodeError:
            print("Update check failed: Invalid response from GitHub API.")
            raise ValueError("Invalid JSON response from GitHub API.")

    def _is_newer_version_sync(self, current_version: str, latest_version: str) -> bool:
        """ Compares two version strings (e.g., '1.2.3'). Handles 'v' prefix. """
        try:
            current_parts = list(map(int, current_version.lstrip('v').split('.')))
            latest_parts = list(map(int, latest_version.lstrip('v').split('.')))

            for i in range(max(len(current_parts), len(latest_parts))):
                c_part = current_parts[i] if i < len(current_parts) else 0
                l_part = latest_parts[i] if i < len(latest_parts) else 0
                if l_part > c_part:
                    return True
                if l_part < c_part:
                    return False
            return len(latest_parts) > len(current_parts)
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not compare version numbers ('{current_version}', '{latest_version}'). Error: {e}")
            return False