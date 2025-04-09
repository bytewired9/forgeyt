"""Initialize Standard Configurations"""
from os import path, getenv, makedirs
from json import load, JSONDecodeError

appdata_path = getenv("APPDATA")
CURRENT_VERSION = "3.0.0"
prompt = input
config_folder = path.join(appdata_path, "ForgeYT")
config_file = path.join(config_folder, "config.json")
# In utils/config.py or the fallback section in main_window.py
DEFAULT_SETTINGS = {
    "theme": "system",
    "download_path": "./video_downloads/",
    "open_folder_after_download": True, # Default for the HOME page checkbox initial state
    # --- New Defaults ---
    "check_for_updates_on_startup": True,
    "clear_console_before_download": False,
    # Metadata/Subs Defaults (used to initialize home page controls)
    "default_keep_original": False,
    "default_embed_metadata": True,
    "default_embed_chapters": True,
    "default_embed_thumbnail": True, # Usually desired for video/audio
    "default_write_infojson": False,
    "default_download_subtitles": False,
    "default_subtitle_langs": "en", # Default language if downloading subs
    "default_embed_subs": False,
    "default_autosubs": False,
    # Network Defaults
    "default_rate_limit": "", # Empty means no limit
    # YouTube Defaults
    "default_sponsorblock": "None", # Options: "None", "Skip", "Mark"
    # Advanced
    "ffmpeg_path_override": "", # Empty means use bundled/system path
    "ffprobe_path_override": "", # Empty means use bundled/system path
}
def makeconfig():
    if not path.exists(config_folder):
        makedirs(config_folder)

def load_config():
    makeconfig()
    if not path.exists(config_file):
        return DEFAULT_SETTINGS
    with open(config_file, "r", encoding="utf-8") as f:
        try:
            return load(f)
        except JSONDecodeError:
            # If there's an error, return a default configuration
            return DEFAULT_SETTINGS

config_data = load_config()
download_path = config_data["download_path"]
windowTheme = config_data["theme"]

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        from sys import _MEIPASS
    except ImportError:
        _MEIPASS = None
    base_path = _MEIPASS if _MEIPASS is not None else path.abspath(".")
    return path.join(base_path, relative_path)
