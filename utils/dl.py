from .hooker import hooker
from os import path
from yt_dlp import YoutubeDL
from subprocess import run
from vars import filetypes
from .config import load_config

def download(yturl, ftype, app_queue, self):
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

    app_queue.put(("update_console", f"Youtube URL: {yturl}"))

    ydl_opts = {
        "outtmpl": f"{convert_to_absolute(download_path)}\\%(uploader)s - %(title)s.{fileext}",
        "ignoreerrors": True,
        "postprocessors": [],
        "progress_hooks": [hooker]
    }

    if audio:
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = f"bestvideo[ext={fileext}]+bestaudio[ext=m4a]/best"

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([yturl])
            app_queue.put(("update_console", "Completed."))


            fixedpath = path.normpath(convert_to_absolute(download_path))
            run(["explorer", fixedpath])

        except Exception as e:
            app_queue.put(("update_console", f"Error during processing: {str(e)}"))
            self.show_custom_messagebox("Error", f"Error during processing: {str(e)}")
        return self.cleanup_after_thread()