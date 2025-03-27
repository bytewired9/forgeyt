"""dl.py enables ForgeYT to actually download things"""
from os import path
from subprocess import run
import sys
from yt_dlp import YoutubeDL
from vars import filetypes
from .config import load_config

def download(yturl, ftype, app_queue, doexplorer, self):
    """Yeah this just downloads stuff. pylints forcing me to type this"""
    def convert_to_absolute(p):
        # If the path starts with ./ or ../ then join it with the executable's directory.
        if p.startswith(("./", "../")):
            # Use the folder of the executable if frozen (e.g., when bundled with PyInstaller),
            # otherwise use the folder of the current file.
            base_path = path.dirname(sys.executable) if getattr(sys, 'frozen', False) else path.dirname(__file__)
            return path.abspath(path.join(base_path, p))
        return p

    config_data = load_config()
    download_path = config_data["download_path"]

    default_filetype_data = filetypes["mp3"]

    filetype = filetypes.get(ftype, default_filetype_data)["filetype"]
    fileext = filetypes.get(ftype, default_filetype_data)["fileext"]
    audio = filetypes.get(ftype, default_filetype_data)["audio"]
    codec = filetypes.get(ftype, default_filetype_data)["codec"]
    app_queue.put(("update_console", f"Youtube URL: {yturl}"))

    ydl_opts = {
        "outtmpl": f"{convert_to_absolute(download_path)}\\%(uploader)s - %(title)s.%(ext)s",
        "ignoreerrors": False,
        "no-mtime": True,
    }
    app_queue.put(("update_console", f"Audio = {audio}"))
    app_queue.put(("update_console", f"{filetype}"))
    app_queue.put(("update_console", f"{codec}"))

    if audio is True:
        # Let yt-dlp pick the best audio, then convert
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,         # e.g., mp3
            "preferredquality": "192"
        }]
    else:
        # Let yt-dlp pick the best video + best audio, then convert
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": fileext       # e.g., mp4
        }]


    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([yturl])
            app_queue.put(("update_console", "Completed."))

            fixedpath = path.normpath(convert_to_absolute(download_path))
            if doexplorer.get() == "True":
                run(["explorer", fixedpath], check=False)

        except Exception as e:
            app_queue.put(("update_console", f"Error during processing: {str(e)}"))
            self.show_custom_messagebox("Error", f"Error during processing: {str(e)}")
        return self.cleanup_after_thread()
