"""Initialize Standard Configurations"""
from os import path, getenv, makedirs
from json import load, JSONDecodeError

appdata_path = getenv("APPDATA")
CURRENT_VERSION = "2.3.6"
prompt = input
config_folder = path.join(appdata_path, "ForgeYT")
config_file = path.join(config_folder, "config.json")
DEFAULT_SETTINGS = {"theme": "system", "download_path": "./video_downloads"}

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
