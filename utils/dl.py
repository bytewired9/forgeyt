import os
import sys
import threading
import re
import subprocess
from yt_dlp import YoutubeDL, DownloadError

try:
    # Attempt to import from your project structure
    from vars import filetypes
    from utils.config import load_config
except ImportError:
    # Fallback definitions if imports fail (useful for testing/standalone)
    print("Warning: Could not import vars/config from project structure. Using placeholder definitions.")
    filetypes = {
        "mp3": {"filetype": "mp3", "fileext": "mp3", "audio": True, "codec": "mp3"},
        "m4a": {"filetype": "m4a", "fileext": "m4a", "audio": True, "codec": "aac"},
        "mp4": {"filetype": "mp4", "fileext": "mp4", "audio": False, "codec": "h264"}, # Example video codec
        "webm": {"filetype": "webm", "fileext": "webm", "audio": False, "codec": "vp9"}, # Example video codec
        # Add other formats your application supports
    }
    def load_config():
        # Basic fallback config
        return {"download_path": os.path.join(os.path.expanduser("~"), "Downloads")}

# --- Mapping for UI Audio Quality strings to bitrate values ---
audio_bitrate_map = {
    "Best (≈192k)": '192',
    "High (128k)": '128',
    "Medium (96k)": '96',
    "Low (64k)": '64',
    # Add more if needed, ensure 'Best' exists or handle appropriately
}

class FFmpegLogger:
    def __init__(self, progress_callback):
        self.progress_callback = progress_callback

    def debug(self, msg):
        self.progress_callback.emit(f"[ffmpeg-debug] {msg}")
    def info(self, msg):
        self.progress_callback.emit(f"[ffmpeg-info] {msg}")
    def warning(self, msg):
        self.progress_callback.emit(f"[ffmpeg-warning] {msg}")
    def error(self, msg):
        self.progress_callback.emit(f"[ffmpeg-error] {msg}")

# --- Custom Exception for Cancellation ---
class DownloadCancelled(Exception):
    """Custom exception raised when download is cancelled via stop_event."""
    pass

# --- Helper to convert relative paths to absolute ---
def _convert_to_absolute(p):
    """Converts potentially relative paths to absolute paths."""
    p_expanded = os.path.expanduser(p) # Expand ~ first
    if os.path.isabs(p_expanded):
        return p_expanded
    # If still relative, base it relative to the script/executable
    if getattr(sys, 'frozen', False): # Check if running as compiled executable
        base_path = os.path.dirname(sys.executable)
    else: # Running as a script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_path, p_expanded))

# --- ANSI Stripping Regex ---
ANSI_ESCAPE_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences from a string."""
    if isinstance(text, str):
        return ANSI_ESCAPE_REGEX.sub('', text)
    return text # Return unmodified if not a string

# --- Helper function to open file explorer ---
def open_file_explorer(path: str) -> None:
    """Opens the file explorer to the specified directory path."""
    abs_path = os.path.abspath(path)
    print(f"Attempting to open explorer at: {abs_path}") # Debug print
    if not os.path.isdir(abs_path):
        print(f"Error: Path is not a valid directory: {abs_path}")
        return

    try:
        if os.name == "nt": # Windows
             os.startfile(abs_path)
            # The win32com code for reusing windows can be complex and sometimes fail
            # os.startfile is simpler and more reliable generally.
            # Consider adding the win32com logic back if window reuse is critical.
            # import win32com.client
            # try:
            #     shell = win32com.client.Dispatch("Shell.Application")
            #     # Implementation to find and focus existing window...
            #     # Fallback to os.startfile if fails or not found
            # except ImportError:
            #      os.startfile(abs_path)
            # except Exception as e:
            #      print(f"Error using Shell.Application: {e}")
            #      os.startfile(abs_path) # Fallback
        elif sys.platform == "darwin": # macOS
            subprocess.run(["open", abs_path], check=True)
        else: # Linux and other Unix-like
            subprocess.run(["xdg-open", abs_path], check=True)
    except FileNotFoundError:
        print(f"Error: Could not find utility to open file explorer (startfile/open/xdg-open).")
    except subprocess.CalledProcessError as e:
        print(f"Error opening file explorer: {e}")
    except Exception as e:
        print(f"An unexpected error occurred opening the file explorer: {e}")


# --- Main Download Function ---
def download(url: str, filetype_key: str, progress_callback: 'Signal', # Assuming Signal is a Qt Signal or similar callback emitter
             open_explorer_flag: bool, stop_event: threading.Event,
             # --- Optional Parameters ---
             video_quality: str = 'Best',
             audio_quality: str = 'Best (≈192k)', # Default audio quality
             # *** ADDED: Codec parameters ***
             video_codec: str | None = None,
             audio_codec: str | None = None,
             # *** END ADDED ***
             embed_thumbnail: bool = False,
             playlist_range: str = '',
             playlist_reverse: bool = False,
             filename_template: str | None = None, # Use None for default yt-dlp template
             keep_original: bool = False,
             embed_metadata: bool = False,
             embed_chapters: bool = False,
             write_infojson: bool = False,
             download_subtitles: bool = False,
             subtitle_langs: str = 'en', # Default subtitle language
             embed_subs: bool = False,
             autosubs: bool = False,
             rate_limit: str | None = None,
             cookie_file: str | None = None,
             sponsorblock_choice: str = 'None' # Options: 'None', 'Skip Sponsor Segments', 'Mark Sponsor Segments'
             ):
    """
    Downloads video/audio using yt-dlp with extensive options and progress reporting.

    Args:
        url (str): The URL of the video or playlist.
        filetype_key (str): The key corresponding to the desired format in the `filetypes` dict (e.g., 'mp3', 'mp4').
        progress_callback: A callable (like a Qt Signal's emit method) to send progress updates (strings).
        open_explorer_flag (bool): If True, open the download directory after successful completion.
        stop_event (threading.Event): An event used to signal cancellation from another thread.
        video_quality (str): Desired video quality (e.g., '1080p', '720p', 'Best').
        audio_quality (str): Desired audio quality string (maps via audio_bitrate_map).
        video_codec (str | None): Specific video codec to use for conversion (e.g., 'h264', 'vp9'). None for auto/default.
        audio_codec (str | None): Specific audio codec to use for conversion (e.g., 'aac', 'mp3'). None for auto/default.
        embed_thumbnail (bool): Embed thumbnail in the audio file (if applicable).
        playlist_range (str): Specific items to download from a playlist (e.g., '1,3-5,10').
        playlist_reverse (bool): Download playlist items in reverse order.
        filename_template (str | None): Custom output filename template (yt-dlp format).
        keep_original (bool): Keep the original downloaded file(s) before post-processing.
        embed_metadata (bool): Embed metadata (like title, artist) into the file.
        embed_chapters (bool): Embed chapter markers if available.
        write_infojson (bool): Write video metadata to a separate .info.json file.
        download_subtitles (bool): Download subtitles.
        subtitle_langs (str): Comma-separated list of subtitle languages (e.g., 'en,es').
        embed_subs (bool): Embed subtitles into the video file (if downloading video and subs).
        autosubs (bool): Download automatically generated subtitles if no manual ones are found.
        rate_limit (str | None): Download speed limit (e.g., '50K', '1M').
        cookie_file (str | None): Path to a cookies file for accessing restricted content.
        sponsorblock_choice (str): How to handle SponsorBlock segments.

    Returns:
        str | None: The absolute path to the final downloaded file, or None if cancelled or failed critically.

    Raises:
        DownloadCancelled: If the stop_event is set during the process.
        DownloadError: If yt-dlp encounters a specific download or processing error.
        OSError: If the download directory cannot be created.
        ValueError: If the filetype_key is invalid.
        Exception: For other unexpected errors.
    """
    final_filepath = None
    max_percentage_reported = 0.0 # Track max progress for potential resets

    # --- Progress Hook for yt-dlp ---
    def progress_hook(d):
        nonlocal final_filepath
        nonlocal max_percentage_reported

        if stop_event.is_set():
            raise DownloadCancelled("Download cancelled by user signal.")

        status = d.get('status')

        if status == 'downloading':
            percent_str = strip_ansi(d.get('_percent_str', '0.0%')).strip()
            try:
                # Attempt to get a reliable float percentage
                current_percentage_float = float(percent_str.replace('%', ''))
            except ValueError:
                progress_callback.emit(f"\nWarning: Could not parse percentage: {percent_str}. Using last known max.")
                current_percentage_float = max_percentage_reported # Use last good value on error

            # --- Logic to handle potential percentage resets (e.g., multiple fragments/downloads) ---
            # If the current percentage is significantly lower than the max reported (and not zero),
            # it might indicate a new stage (like downloading audio after video), so reset max.
            if current_percentage_float < max_percentage_reported and max_percentage_reported > 5.0 and current_percentage_float > 0.1:
                 # Heuristic: If drop is large, might be a new file/stream segment. Reset max.
                 if (max_percentage_reported - current_percentage_float) > 50.0:
                      max_percentage_reported = current_percentage_float
            # Update max percentage if current is higher
            if current_percentage_float >= max_percentage_reported:
                 max_percentage_reported = current_percentage_float

            # Always display the current max reported percentage for a smoother progress bar experience
            display_percentage_str = f"{max_percentage_reported:.1f}%"

            # --- Extract other progress info ---
            total_bytes_str = strip_ansi(d.get('_total_bytes_str', 'N/A'))
            speed_str = strip_ansi(d.get('_speed_str', 'N/A'))
            eta_str = strip_ansi(d.get('_eta_str', 'N/A'))
            frag_info = ""
            if 'fragment_index' in d and 'fragment_count' in d:
                frag_info = f" (frag {d['fragment_index']}/{d['fragment_count']})"

            # Emit formatted progress line - use \r for single-line updating
            progress_line = f"\r[download] {display_percentage_str:>6} of ~{total_bytes_str} at {speed_str} ETA {eta_str}{frag_info}"
            progress_callback.emit(progress_line)

        elif status == 'finished':
            # Store the final filename when download completes
            final_filepath = d.get('filename') or d.get('info_dict', {}).get('_filename')
            # Ensure 100% is shown on completion
            final_max = max(max_percentage_reported, 100.0)
            final_progress_line = f"\r[download] {final_max:>6.1f}% of ~{strip_ansi(d.get('_total_bytes_str', 'N/A'))} completed."
            progress_callback.emit(final_progress_line)
            progress_callback.emit("") # New line after progress bar
            progress_callback.emit(strip_ansi(f"Source download finished: {os.path.basename(final_filepath or 'Unknown file')}"))
            max_percentage_reported = 0.0 # Reset for potential next file in playlist or postprocessing

        elif status == 'error':
            progress_callback.emit("\nError reported during download hook.")
            max_percentage_reported = 0.0 # Reset on error

    # --- Postprocessor Hook for yt-dlp ---
    def postprocessor_hook(d):
        nonlocal final_filepath
        if stop_event.is_set():
            raise DownloadCancelled("Download cancelled during postprocessing.")

        status = d.get('status')
        pp_name = d.get('postprocessor', 'step')

        if status == 'started':
             progress_callback.emit(strip_ansi(f"[PostProcessing] Starting '{pp_name}'..."))
        elif status == 'processing':
             # yt-dlp doesn't usually provide detailed progress for FFmpeg steps here
             # You could emit a generic "processing" message if needed
             pass # progress_callback.emit(strip_ansi(f"[PostProcessing] Processing '{pp_name}'..."))
        elif status == 'finished':
             # Update final_filepath if postprocessor modifies it (e.g., conversion changes extension)
             final_filepath = d.get('info_dict', {}).get('filepath') or final_filepath # Use 'filepath' if available after PP
             progress_callback.emit(strip_ansi(f"[PostProcessing] Finished '{pp_name}'."))
        elif status == 'error':
             progress_callback.emit(strip_ansi(f"\n[PostProcessing] Error occurred during '{pp_name}'."))

    # --- Main Download Logic ---
    try:
        progress_callback.emit(f"Preparing download for: {url}")

        # --- Load Config and Setup Paths ---
        config_data = load_config()
        # Ensure download_path from config is absolute
        download_path = _convert_to_absolute(config_data["download_path"])

        if not os.path.isdir(download_path):
            progress_callback.emit(f"Download directory does not exist. Creating: {download_path}")
            try:
                os.makedirs(download_path, exist_ok=True)
                progress_callback.emit(f"Successfully created directory: {download_path}")
            except OSError as e:
                # Raise a more specific OSError if directory creation fails
                raise OSError(f"Failed to create download directory '{download_path}': {e}")

        # --- Get Format Details ---
        format_info = filetypes.get(filetype_key)
        if not format_info:
            raise ValueError(f"Invalid file type key specified: '{filetype_key}'. Check `filetypes` definition.")

        fileext = format_info.get("fileext", "unknown")
        audio_only = format_info.get("audio", False)
        # target_codec_from_filetype is the *default* codec from filetypes, may be overridden by passed audio/video_codec args
        target_codec_from_filetype = format_info.get("codec")

        # Get preferred audio quality bitrate (string)
        preferred_audio_quality_k = audio_bitrate_map.get(audio_quality)
        if not preferred_audio_quality_k:
             progress_callback.emit(f"Warning: Audio quality '{audio_quality}' not found in map. Using default '192k'.")
             preferred_audio_quality_k = '192' # Fallback bitrate

        # --- Log Selected Options ---
        progress_callback.emit(f"Selected format: {filetype_key.upper()} ({'Audio Only' if audio_only else 'Video'})")
        progress_callback.emit(f"Target file extension: .{fileext}")
        progress_callback.emit(f"Download path: {download_path}")

        if not audio_only:
            progress_callback.emit(f"Video Quality Preference: {video_quality}")
            if video_codec: # Log the specifically requested codec
                progress_callback.emit(f"Requested Video Codec: {video_codec}")
            elif target_codec_from_filetype: # Log the default if no specific one requested
                 progress_callback.emit(f"Default Video Codec (from filetype): {target_codec_from_filetype}")
            else:
                 progress_callback.emit("Video Codec: Default (Let FFmpeg/yt-dlp decide)")
        else:
            progress_callback.emit(f"Audio Quality Preference: {audio_quality} (Target Bitrate: {preferred_audio_quality_k}k)")
            if audio_codec: # Log the specifically requested codec
                progress_callback.emit(f"Requested Audio Codec: {audio_codec}")
            elif target_codec_from_filetype: # Log the default if no specific one requested
                progress_callback.emit(f"Default Audio Codec (from filetype): {target_codec_from_filetype}")
            else:
                 progress_callback.emit("Audio Codec: Default (Let FFmpeg decide based on extension/quality)")


        if playlist_range: progress_callback.emit(f"Playlist Items: {playlist_range}")
        if playlist_reverse: progress_callback.emit("Playlist Order: Reversed")
        if filename_template: progress_callback.emit(f"Filename Template: {filename_template}")
        else: progress_callback.emit("Filename Template: Default (uploader - title.ext)")
        if keep_original: progress_callback.emit("Option: Keep Original Enabled")
        if embed_metadata: progress_callback.emit("Option: Embed Metadata Enabled")
        if embed_chapters: progress_callback.emit("Option: Embed Chapters Enabled")
        if write_infojson: progress_callback.emit("Option: Write info.json Enabled")
        if embed_thumbnail: progress_callback.emit("Option: Embed Thumbnail Enabled") # Log always if checked
        if download_subtitles:
            progress_callback.emit(f"Option: Download Subs Enabled (Langs: {subtitle_langs}, AutoSubs: {autosubs}, Embed: {embed_subs})")
        if rate_limit: progress_callback.emit(f"Option: Rate Limit: {rate_limit}")
        if cookie_file: progress_callback.emit(f"Option: Using Cookie File: {os.path.basename(cookie_file)}")
        if sponsorblock_choice != 'None': progress_callback.emit(f"Option: SponsorBlock: {sponsorblock_choice}")

        # --- Build yt-dlp Options Dictionary ---
        ydl_opts = {
            "ignoreerrors": False, # Stop on error for single downloads; consider True for playlists if needed
            "no_warnings": False, # Show warnings from yt-dlp
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
            "quiet": True, # Suppress yt-dlp console output (we handle it via hooks)
            "no_mtime": True, # Don't modify file timestamps
            "outtmpl": os.path.join(download_path, '%(uploader)s - %(title)s.%(ext)s'), # Default template
            "playlistreverse": playlist_reverse,
            "playlist_items": playlist_range if playlist_range else None,
            "noplaylist": False if playlist_range or ('list=' in url and '/watch?' in url) else True, # Handle single video from playlist URL better
            "keepvideo": keep_original,
            "restrictfilenames": True,
            "embedmetadata": embed_metadata,
            "embedchapters": embed_chapters,
            "writethumbnail": embed_thumbnail, # Tell yt-dlp to download the thumbnail if needed for embedding
            "writeinfojson": write_infojson,
            "writesubtitles": download_subtitles,
            "writeautomaticsub": download_subtitles and autosubs,
            "subtitleslangs": subtitle_langs.split(',') if download_subtitles and subtitle_langs else None,
            "subtitlesformat": "srt/best", # Common subtitle format
            "embedsubtitles": download_subtitles and embed_subs and not audio_only, # Only embed in video
            "ratelimit": rate_limit,
            "cookiefile": cookie_file,
            "sponsorblock_remove": ['sponsor'] if sponsorblock_choice == 'Skip Sponsor Segments' else None, # Specify category if needed
            "sponsorblock_mark": ['sponsor'] if sponsorblock_choice == 'Mark Sponsor Segments' else None, # Specify category if needed
            "postprocessors": [], # Initialize postprocessors list
            'postprocessor_args': {}, # Initialize as dict for easier merging later
            # 'ffmpeg_location': '/path/to/ffmpeg', # Optional: if ffmpeg/ffprobe aren't in PATH
        }

        # Initialize FFmpeg logger and verbose logging
        ydl_opts['logger'] = FFmpegLogger(progress_callback)
        ydl_opts.setdefault('postprocessor_args', {}).setdefault('ffmpeg', []).extend(['-loglevel', 'verbose']) # Use dict structure

        # Apply custom filename template if provided
        if filename_template:
            ydl_opts["outtmpl"] = os.path.join(download_path, filename_template)

        # --- Configure Postprocessors and Format Selection ---

        # Add thumbnail embedder if requested (works for audio formats supporting it)
        if embed_thumbnail:
            ydl_opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False # Let yt-dlp handle fetching if needed
            })

        if audio_only:
            ydl_opts["format"] = "bestaudio/best"
            # *** MODIFIED: Use passed audio_codec if available ***
            preferred_codec = audio_codec if audio_codec else (target_codec_from_filetype if target_codec_from_filetype else fileext)
            progress_callback.emit(f"Using audio codec for FFmpeg: {preferred_codec}") # Log actual codec used
            pp_audio = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": preferred_codec,
                "preferredquality": preferred_audio_quality_k,
            }
            ydl_opts['postprocessors'].append(pp_audio)
        else: # Video
            quality_filter = ""
            if video_quality != "Best":
                height = "".join(filter(str.isdigit, video_quality))
                if height:
                    quality_filter = f"[height<=?{height}]"

            # Prefer mp4 container for video, then webm, then best overall
            # This format string tries to get compatible streams first
            ydl_opts["format"] = (
                 f"bestvideo{quality_filter}[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo{quality_filter}[ext=webm][vcodec^=vp9]+bestaudio[ext=opus]/bestvideo{quality_filter}+bestaudio/best{quality_filter}"
            )

            # Determine if conversion is needed (extension mismatch OR specific codec requested)
            # This check is heuristic. yt-dlp might still convert if merged streams aren't compatible with the container.
            needs_conversion = (fileext not in ['mp4', 'mkv', 'webm']) or video_codec is not None # Trigger conversion if specific codec is requested

            if needs_conversion:
                progress_callback.emit("Video conversion postprocessor will be used.")
                pp_video = {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': fileext, # Note: yt-dlp uses 'preferedformat' spelling
                }
                ydl_opts['postprocessors'].append(pp_video)

                # Add FFmpeg arguments via the TOP-LEVEL postprocessor_args dict structure
                ffmpeg_args = ydl_opts.setdefault('postprocessor_args', {}).setdefault('ffmpeg', [])

                # *** MODIFIED: Use passed video_codec if available ***
                if video_codec:
                    progress_callback.emit(f"Adding FFmpeg argument: -c:v {video_codec}")
                    ffmpeg_args.extend(['-c:v', video_codec])
                # else: # If converting container but not codec, copy video stream
                #     ffmpeg_args.extend(['-c:v', 'copy'])

                # Handle audio codec during video conversion
                audio_codec_for_video = audio_codec if audio_codec else 'aac' # Default to AAC for compatibility
                if audio_codec_for_video == 'copy':
                     progress_callback.emit("Adding FFmpeg argument: -c:a copy")
                     ffmpeg_args.extend(['-c:a', 'copy'])
                else:
                     progress_callback.emit(f"Adding FFmpeg arguments: -c:a {audio_codec_for_video} -b:a {preferred_audio_quality_k}k")
                     ffmpeg_args.extend(['-c:a', audio_codec_for_video, '-b:a', f'{preferred_audio_quality_k}k'])

        # --- Final Cleanup of Options (using dict for postprocessor_args) ---
        # Convert postprocessor_args dict back to list format expected by yt-dlp >= 2023.06.22
        if 'postprocessor_args' in ydl_opts and ydl_opts['postprocessor_args']:
             args_list = []
             for pp_key, pp_args in ydl_opts['postprocessor_args'].items():
                  if pp_args: # Only add if there are args for this key
                    # Use subprocess.list2cmdline for robust quoting on Windows
                    # Use ' '.join for Linux/macOS (less robust but common)
                    cmd_line = subprocess.list2cmdline(pp_args) if sys.platform == 'win32' else ' '.join(map(str, pp_args))
                    args_list.append(f"{pp_key}:{cmd_line}") # Format as KEY:ARGS_STRING
             if args_list:
                  ydl_opts['postprocessor_args'] = args_list
             else:
                  del ydl_opts['postprocessor_args'] # Remove if empty
        elif 'postprocessor_args' in ydl_opts: # Ensure removal if initialized but remained empty
            del ydl_opts['postprocessor_args']

        # Remove other empty/None options
        final_ydl_opts = {}
        for k, v in ydl_opts.items():
            # Keep False values if they are valid options (e.g., ignoreerrors=False might be needed)
            # Check specifically for None, empty strings, empty lists/tuples
            if v is None: continue
            if isinstance(v, (str, list, tuple)) and not v: continue
            # Add bools directly (True/False)
            final_ydl_opts[k] = v

        # Specifically remove 'postprocessors' if it ended up empty after logic
        if 'postprocessors' in final_ydl_opts and not final_ydl_opts['postprocessors']:
            del final_ydl_opts['postprocessors']


        # --- Execute Download ---
        progress_callback.emit("Starting yt-dlp download process...")
        # For debugging: print the final options being passed
        try:
            # Attempt to serialize, converting non-serializable items to strings
            opts_str = json.dumps(final_ydl_opts, indent=2, default=lambda o: f"<<non-serializable: {type(o).__name__}>>")
            progress_callback.emit(f"Final yt-dlp Options:\n{opts_str}")
        except Exception as json_err:
            progress_callback.emit(f"Could not serialize final options for logging: {json_err}")
            progress_callback.emit(f"Options (raw): {final_ydl_opts}")


        with YoutubeDL(final_ydl_opts) as ydl:
            if stop_event.is_set():
                raise DownloadCancelled("Download cancelled just before starting yt-dlp.")

            # Ensure directory exists one last time (might be redundant but safe)
            os.makedirs(download_path, exist_ok=True)

            # Start the download and processing
            return_code = ydl.download([url])
            progress_callback.emit(f"yt-dlp download() returned: {return_code}") # Log return code

        # --- Post-Download Handling ---
        if stop_event.is_set():
            # Even if ydl.download finished, check cancellation flag again
            progress_callback.emit("\nDownload process completed, but cancellation was requested.")
            # Optional: attempt cleanup of potentially incomplete files based on final_filepath
            return None # Indicate cancellation

        # Check final_filepath determined by hooks
        if final_filepath and os.path.exists(final_filepath):
            progress_callback.emit("-------------------------------------")
            progress_callback.emit(f"Successfully downloaded and processed:")
            progress_callback.emit(f"File: {os.path.basename(final_filepath)}")
            progress_callback.emit(f"Path: {os.path.dirname(final_filepath)}")
            progress_callback.emit("-------------------------------------")
            if open_explorer_flag:
                # Open the containing directory
                open_file_explorer(os.path.dirname(final_filepath))
            return os.path.abspath(final_filepath) # Return the full path
        elif final_filepath:
             progress_callback.emit(f"\nError: Download/processing finished, but the expected output file was not found at '{final_filepath}'.")
             raise DownloadError("Output file missing after download/processing completion.")
        elif return_code == 0: # Check return code if filepath wasn't found by hooks
             progress_callback.emit(f"\nWarning: Download likely succeeded (yt-dlp code 0), but the final file path could not be reliably determined by hooks. Check download folder: {download_path}")
             # Try to guess based on template (less reliable)
             # This part is tricky without knowing the exact title/uploader
             return download_path # Return directory as a fallback? Or None?
        else:
            # This case might happen if the hooks didn't capture the filename or download failed early
            progress_callback.emit(f"\nError: Download finished, but the final file path could not be determined and yt-dlp return code was non-zero ({return_code}).")
            raise DownloadError(f"Could not determine output file path after download (Code: {return_code}).")

    # --- Exception Handling ---
    except DownloadCancelled as e:
        progress_callback.emit(f"\nOperation Cancelled: {e}")
        # Do not re-raise as Exception, let it propagate as DownloadCancelled if needed higher up
        # Or just return None to indicate cancellation gracefully
        return None
    except DownloadError as e:
        # Handle errors reported directly by yt-dlp (or raised by our checks)
        clean_error_msg = strip_ansi(str(e))
        # Log the specific yt-dlp error
        progress_callback.emit(f"\nDownload Error: {clean_error_msg}")
        # Re-raise to signal failure upstream
        raise # Keep original exception type for worker handling
    except (OSError, ValueError) as e:
         # Handle specific errors we might raise (directory creation, invalid filetype)
         progress_callback.emit(f"\nConfiguration/Setup Error: {e}")
         raise # Re-raise these specific errors
    except Exception as e:
        # Catch any other unexpected exceptions
        import traceback
        err_trace = traceback.format_exc() # Get the full traceback
        clean_error_msg = strip_ansi(str(e))
        progress_callback.emit(f"\nAn Unexpected Error Occurred: {clean_error_msg}")
        progress_callback.emit(f"Traceback:\n{err_trace}") # Log the traceback for debugging
        # Wrap in a generic Exception to signal unexpected failure
        raise Exception(f"An unexpected error occurred during download: {clean_error_msg}") from e
