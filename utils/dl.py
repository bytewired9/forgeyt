"""dl.py enables ForgeYT to actually download things"""
from os import path
from subprocess import run
from yt_dlp import YoutubeDL
from vars import filetypes
from .config import load_config

def download(yturl, ftype, app_queue, doexplorer, self):
    """Yeah this just downloads stuff. pylints forcing me to type this"""
    def convert_to_absolute(p):
        if p.startswith(("./", "../")):
            return path.abspath(p)
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
        # "verbose": True,
        "no-mtime": True
    }
    app_queue.put(("update_console", f"Audio = {audio}"))
    app_queue.put(("update_console", f"{filetype}"))
    app_queue.put(("update_console", f"{codec}"))

    if audio is True:
        app_queue.put(("update_console", "Audio Path Selected"))
        ydl_opts["format"] = f"bestaudio[acodec={codec}]/best"
        ydl_opts["postprocessors"] = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": codec,
        "preferredquality": "192",
    }]
    else:
        app_queue.put(("update_console", "Video Path Selected"))
        ydl_opts["format"] = f"bestvideo[ext={fileext}][vcodec={codec}]+bestaudio[ext=m4a]/best"

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
    