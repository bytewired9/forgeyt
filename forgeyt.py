
#==========  File Imports  ===========
from os import path, getenv, makedirs
from sys import stdout as sysstdout
from yt_dlp import YoutubeDL 
from urllib.parse import urlparse
from customtkinter import CTkScrollableFrame, NORMAL, CTk, CTkToplevel, CTkComboBox, CTkSegmentedButton, CTkEntry, CTkProgressBar, CTkImage, END, CTkLabel, CTkButton, CTkFrame, set_appearance_mode, CTkTextbox, WORD, DISABLED
from threading import Thread, Event
from json import load, JSONDecodeError, dump
from queue import Queue, Empty
from tkinter import filedialog, StringVar
from pyglet import font as pygfont
from subprocess import run
from PIL import Image
#============ General Configs ============
appdata_path = getenv('APPDATA')
currentversion = '2.0'
prompt = input
config_folder = path.join(appdata_path, 'ForgeYT')
config_file = path.join(config_folder, 'config.json')
if not path.exists(config_folder):
    makedirs(config_folder)

DEFAULT_SETTINGS = {
    "theme": "system",
    "download_path": "./video_downloads"
}

def load_config():
    if not path.exists(config_file):
        return DEFAULT_SETTINGS

    with open(config_file, 'r') as f:
        try:
            return load(f)
        except JSONDecodeError:
            # If there's an error, return a default configuration
            return DEFAULT_SETTINGS



config_data = load_config()
download_path = config_data["download_path"]
windowTheme = config_data["theme"]
#============ General Configs ============

#===========  Check Version  ============
# def versioncheck():
#     response = requests.get('https://squawksquad.net/forgedytversion.txt')
#     data = response.text.strip()
# 
#     if data != currentversion:
#         app_queue.put(("update_console", "ForgeYT Has an update! Downloading Latest Version."))
# 
#         url = 'https://github.com/ForgedCore8/forgeytdeps/releases/latest/download/ForgeYT.exe?raw=true'
#         response = requests.get(url, stream=True)
#         with open('ForgeYT.exe', 'wb') as file:
#             for chunk in response.iter_content(chunk_size=8192):
#                 file.write(chunk)
# 
#         app_queue.put(("update_console", 'File downloaded successfully!'))
#         app_queue.put(("update_console", 'ForgeYT Updated Successfully. Please Reopen ForgeYT!'))
#         exit()
#     else:
#         app_queue.put(("update_console", "Version check: Up to date")
#          doPrompts()
# 
#===========  Check Version  ============
try:
    from sys import _MEIPASS
except ImportError:
    _MEIPASS = None
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = _MEIPASS if _MEIPASS is not None else path.abspath(".")
    return path.join(base_path, relative_path)



filetypes = {
    "mp3": {"filetype": "mp3", "fileext": "mp3", "audio": True},
    "mp4": {"filetype": "mp4", "fileext": "mp4", "audio": False},
    "ogg": {"filetype": "ogg", "fileext": "ogg", "audio": True},
    "vorbis": {"filetype": "vorbis", "fileext": "ogg", "audio": True},
    "avi": {"filetype": "avi", "fileext": "avi", "audio": False},
    "flv": {"filetype": "flv", "fileext": "flv", "audio": False},
    "mkv": { "filetype": "mkv", "fileext": "mkv", "audio": False},
    "mov": { "filetype": "mov", "fileext": "mov", "audio": False},
    "webm": { "filetype": "webm", "fileext": "webm", "audio": False},
    "aac": { "filetype": "aac", "fileext": "aac", "audio": True},
    "aiff": { "filetype": "aiff", "fileext": "aiff", "audio": True},
    "alac": { "filetype": "aiac", "fileext": "aiac", "audio": True},
    "flac": { "filetype": "flac", "fileext": "flac", "audio": True},
    "m4a": { "filetype": "m4a", "fileext": "m4a", "audio": True},
    "mka": { "filetype": "mka", "fileext": "mka", "audio": True},
    "opus": { "filetype": "opus", "fileext": "opus", "audio": True},
    "wav": { "filetype": "wav", "fileext": "wav", "audio": True}
}

def download(yturl, ftype, app_queue, stop_event, self): 
    def convert_to_absolute(path):
        if path.startswith(("./", "../")):
            return path.abspath(path)
        return path
    config_data = load_config()
    download_path = config_data["download_path"]
   
    default_filetype_data = filetypes["mp3"]

    filetype = filetypes.get(ftype, default_filetype_data)["filetype"]
    fileext = filetypes.get(ftype, default_filetype_data)["fileext"]
    audio = filetypes.get(ftype, default_filetype_data)["audio"]

    app_queue.put(("update_console", f'Youtube URL: {yturl}'))
    
    ydl_opts = {
        'outtmpl': f"{convert_to_absolute(download_path)}\\%(artist)s - %(title)s.{fileext}",
        'ignoreerrors': True
    }
    
    if audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': filetype,
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = f'bestvideo[ext={fileext}]+bestaudio[ext={fileext}]/best[ext={fileext}]'
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([yturl])
            app_queue.put(("update_console", "ForgeYT made by ForgedCore8, 2023, SquawkSquad"))
            run(['explorer', convert_to_absolute(download_path)])

        except Exception as e:
            app_queue.put(("update_console", f"Error during processing: {str(e)}"))
            app.show_custom_messagebox("Error", f"Error during processing: {str(e)}")
        return app.cleanup_after_thread()

def restartprompts():
    pass


#===========  Request Prompts  ============

class CustomMessageBox:
    _instance = None  # Class variable to keep track of the current instance

    def __init__(self, root, title, message):
        if CustomMessageBox._instance:  # Check if an instance already exists
            CustomMessageBox._instance.top.destroy()  # Destroy the existing instance

        self.top = CTkToplevel(root)
        self.top.title(title)
        self.top.resizable(False, False)
        CustomMessageBox._instance = self  # Update the class variable
        
        self.label = CTkLabel(self.top, text=message, wraplength=250)
        self.label.pack(padx=10, pady=10)

        self.button = CTkButton(self.top, text="OK", command=self.destroy_messagebox, fg_color=app.buttoncolor, hover_color=app.buttoncolor_hover, width=80)
        self.button.pack(pady=10)
        
        # Make the messagebox transient to the main window
        self.top.transient(root)
        # Ensure that it always stays on top
        self.top.attributes("-topmost", True)

        self.top.update_idletasks()  # Update the GUI tasks

        # Calculate the width and height based on individual widget sizes
        window_width = max(self.top.winfo_width(), self.label.winfo_width() + 20)  # 20 to accommodate padding
        # Add up the heights of individual widgets with padding
        window_height = self.label.winfo_height() + self.button.winfo_height() + 40  # 40 to accommodate padding
        
        # Calculate the center position of the main window
        pos_x = root.winfo_x() + (root.winfo_width() // 2)
        pos_y = root.winfo_y() + (root.winfo_height() // 2)

        # Adjust so that the messagebox is centered on the main window
        center_x = pos_x - (window_width // 2)
        center_y = pos_y - (window_height // 2)

        # Set the new position and dimensions
        self.top.geometry("%dx%d+%d+%d" % (window_width, window_height, center_x, center_y))

    def destroy_messagebox(self):
        CustomMessageBox._instance = None  # Clear the class variable
        self.top.destroy()




    
class App(CTkFrame):
    def flush(self):
        pass      

    def __init__(self, root):
        super().__init__(root)
        set_appearance_mode(windowTheme)
        self.canvas_img = None
        icon_path = resource_path('ForgeYT.ico')
        root.iconbitmap(default=icon_path)
        self.current_page = "none"
        sysstdout = self
        self.root = root
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        self.root.title("ForgeYT")
        self.original_stdout = sysstdout
        self.font_color = ("black", "white")
        self.background_color1 = ('#fafefe','#04251e')
        self.background_color2 = ('#bef8ec', '#031b16')
        self.buttoncolor = ('#d21941','#c83232')
        self.buttoncolor_hover = ('#841029','#970222')
        self.output_buffer = ""
        def register_font(font_path):
            pygfont.add_file(font_path)
            base_name = font_path.split('/')[-1]
            font_name = base_name.rsplit('.', 1)[0]
            return font_name
        self.font_path = resource_path('./LeagueSpartan-Bold.otf')
        self.font_name =  register_font(self.font_path)
        self.left_frame = CTkFrame(self.root, fg_color=self.background_color2)
        self.left_frame.grid(row=0, column=0, sticky='nsew')
        self.right_frame = CTkFrame(root, fg_color=self.background_color1)
        self.right_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=10, pady=10)
        self.root.grid_rowconfigure(0, weight=1)  # Makes the row 0 expand vertically
        self.root.grid_columnconfigure(0, minsize=100)  # First column fixed at 100 pixels
        self.root.grid_columnconfigure(1, minsize=550)  # Second column fixed at 500 pixels
        self.download_thread = None  # To keep track of download thread
        self.url_of_the_profile_page = None
        self.console_output = CTkTextbox(self.right_frame, wrap=WORD, padx=20, pady=20, state=DISABLED)
        self.console_output.grid_forget()
        self.cursor_position = '1.0'
        self.setup_ui()
        self.last_newline_position = END
        self.queue = Queue()
        self.stop_threads = Event()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.check_queue()
        self.loading_label = CTkLabel(self.right_frame, text="Processing...", text_color='white', bg_color='transparent')
        self.loading_label.grid(pady=40)
        self.loading_label.grid_forget()
        self.start_image = CTkImage(light_image=Image.open(resource_path("download.png")), dark_image=Image.open(resource_path("download_dark.png")), size=(40, 40))
        self.start_button = CTkButton(self.right_frame, image=self.start_image, text="", command=self.start_downloading, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover,height=50, width=120)
        self.start_button.grid(pady=40)
        self.start_button.grid_forget()
        self.stop_event = Event()
        self.scalable_elements = {
            'title_label': None,  # We'll store the actual label here later
            'url_label': None,
            'start_button': None
        }
        self.current_font_size = 16  # This would be the initial font size for your elements.
        window_width = root.winfo_width()
        progress_bar_width = int(window_width * 0.9)
        self.progress_bar = CTkProgressBar(
            master=self.right_frame,
            width=progress_bar_width,
            height=20,
            orientation="horizontal",
            mode="determinate"
        )
        self.dropdown_options = [key.upper() for key in filetypes.keys()]
        self.dropdown_menu = CTkComboBox(self.right_frame, values=self.dropdown_options, corner_radius=6)
        self.profile_entry = CTkEntry(self.right_frame, width=30)
        self.profile_entry.grid(row=2, column=0, pady=(5, 5), padx=60, sticky='ew')
        self.profile_entry.grid_forget()  # Initially hide it if the home is not the default screen

        self.show_home()
        self.after_id = None
        



    def show_progress_bar(self):
        # Place the progress bar at the bottom of the main window.
        self.progress_bar.place(relx=0.5, rely=1.0, anchor="s")
        root.update_idletasks()
        
    def close_app(self):
        # Signal all threads to stop
        self.stop_threads.set()

        # If there are other cleanup tasks, perform them here

        # Close the window
        self.root.quit()
        self.root.destroy()

    def show_custom_messagebox(self, title="Message", message="Something happened!"):
        CustomMessageBox(self.root, title, message)

    def start_downloading(self):
        url = self.profile_entry.get()
        filetype = self.dropdown_menu.get().lower()

        # Check if the input is empty or just whitespace
        if not url.strip():
            self.show_custom_messagebox("Error", "Please enter the required input!")
            return

        # Check if the input is a valid URL
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            self.show_custom_messagebox("Error", "Please enter a valid URL!")
            return

        # Start the downloading thread
        self.download_thread = Thread(target=download, args=(url, filetype, self.queue, self.stop_event, self))
        self.download_thread.start()

        # Hide the start button and show the loading label
        self.start_button.grid_forget()
        self.loading_label.grid(pady=40)



    def cleanup_after_thread(self):
        self.progress_bar.place_forget()

        # Hide the loading_label if it's present
        self.loading_label.grid_forget()
        self.profile_entry.delete(0, END)
        self.dropdown_menu.set("MP3")

        # If we are in the home page and the download thread is not alive, show the start button
        if self.current_page == "home" and not self.download_thread.is_alive():
            self.start_button.grid(pady=40)
        self.stop_event.clear()




    def check_queue(self):
        try:
            while True:  # This loop will keep checking the queue until it's empty
                message, data = self.queue.get_nowait()  # Non-blocking get
                if message == "update_console":
                    self.write(data, from_queue=True)
        except Empty:  # Raised when the queue is empty
            pass
        # Schedule the next check
        self.root.after(1, self.check_queue)

    

    def setup_ui(self):
        button_height = 57
        button_padding_y = 5
        self.forgeyt_image = CTkImage(Image.open(resource_path("ForgeYT.png")), size=(120, 120))
        self.home_image = CTkImage(light_image=Image.open(resource_path("Home.png")), dark_image=Image.open(resource_path("Home_dark.png")), size=(button_height-10, button_height-10))
        self.settings_image = CTkImage(light_image=Image.open(resource_path("Settings.png")), dark_image=Image.open(resource_path("Settings_dark.png")), size=(button_height-10, button_height-10))
        self.about_image = CTkImage(light_image=Image.open(resource_path("About.png")), dark_image=Image.open(resource_path("About_dark.png")), size=(button_height-10, button_height-10))
        self.console_image = CTkImage(light_image=Image.open(resource_path("Console.png")), dark_image=Image.open(resource_path("Console_dark.png")), size=(button_height-10, button_height-10))
        self.image_label = CTkLabel(self.left_frame, image=self.forgeyt_image, text="")
        self.image_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.image_label_label = CTkLabel(self.left_frame, text="ForgeYT", font=(self.font_name, 30, "bold"), text_color=self.font_color, bg_color="transparent")
        self.image_label_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(1, 10))
        self.home_button = CTkButton(self.left_frame, image=self.home_image, text="", command=self.show_home, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover, height=button_height)
        self.home_button.grid(row=2, column=0, sticky="ew", padx=10, pady=button_padding_y)
        self.settings_button = CTkButton(self.left_frame, image=self.settings_image, text="", command=self.show_settings, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover, height=button_height)
        self.settings_button.grid(row=3, column=0, sticky="ew", padx=10, pady=button_padding_y)
        self.about_button = CTkButton(self.left_frame, image=self.about_image, text="", command=self.show_about, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover, height=button_height)
        self.about_button.grid(row=4, column=0, sticky="ew", padx=10, pady=button_padding_y)
        self.console_button = CTkButton(self.left_frame, image=self.console_image, text="", command=self.show_console, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover, height=button_height)
        self.console_button.grid(row=5, column=0, sticky="ew", padx=10, pady=button_padding_y)

        # To make the buttons expand horizontally
        self.left_frame.grid_columnconfigure(0, weight=1)

    def adjust_font(self, event):
        if event.widget == self.root:
            new_size = int(event.width / 40)

            if new_size != self.current_font_size:
                self.current_font_size = new_size
                for widget in self.scalable_elements.values():
                    if widget:
                        widget.config(font=("League Spartan", self.current_font_size))

                self.root.after(500, self.root.update_idletasks)

    def show_home(self):
        self.current_page = "home"
        # Clear existing widgets
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()
        # Configure rows and columns for scalability
        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=0)  # Make it absolute
        self.right_frame.grid_rowconfigure(2, weight=0)  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(0, weight=1)  # Letting the column still expand horizontally
        # Padding for the entire frame
        self.right_frame['padx'] = 20
        self.right_frame['pady'] = 20
        # Title Label
        self.scalable_elements['title_label'] = CTkLabel(self.right_frame, text="ForgeYT", font=(self.font_name, 50, "bold"), text_color=self.font_color, bg_color="transparent")
        self.scalable_elements['title_label'].grid(row=0, column=0, pady=50, sticky='nsew')
        # Profile URL Input Label
        self.scalable_elements['url_label'] = CTkLabel(self.right_frame, text="Enter Video URL", font=(self.font_name, 20), text_color=self.font_color, bg_color="transparent")
        self.scalable_elements['url_label'].grid(row=1, column=0, pady=(0, 10),sticky='nsew') # Adjust the top padding to be more than the bottom padding

        # Entry Box for Profile URL
        self.profile_entry.grid(row=2, column=0, pady=(5, 5), padx=60, sticky='ew')  # Adjust the bottom padding to be more than the top padding
        # Check if a download is in progress; Display appropriate button
        # Dropdown Menu (Combobox) below the Entry Box
        self.dropdown_label = CTkLabel(self.right_frame, text="Select File Type", font=(self.font_name, 20), text_color=self.font_color, bg_color="transparent")
        self.dropdown_label.grid(row=3, column=0, pady=(5, 5), sticky='nsew')

        self.dropdown_menu.grid(row=4, column=0, pady=5, padx=60, sticky='ew')  # Adjust padding and placement accordingly
        if self.download_thread and self.download_thread.is_alive():
            self.loading_label.grid(row=5, column=0, pady=40)
        else:
            self.start_button.grid(row=5, column=0, pady=40)

    def limit_entry_size(self, *args):
        value = self.entry_var.get()
        if len(value) > 40:
            self.entry_var.set(value[:40])

    def show_settings(self):
        config_data = load_config()
        download_path = config_data["download_path"]
        self.right_frame.grid_columnconfigure(0, weight=1)
        windowTheme = config_data["theme"]
        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=3)  # Make it absolute
        # self.right_frame.grid_rowconfigure(2, weight=0)  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(0, weight=1)  # Letting the column still expand horizontally

        def reset_to_default():
            # Update the config file
            with open(config_file, 'w') as f:
                dump(DEFAULT_SETTINGS, f, indent=4)

            # Update the GUI elements
            self.filepath_entry.delete(0, END)
            self.filepath_entry.insert(0, DEFAULT_SETTINGS["download_path"])
            self.theme_var.set(DEFAULT_SETTINGS["theme"])
            set_appearance_mode(DEFAULT_SETTINGS["theme"])
            
            # Inform the user
            self.show_custom_messagebox("Success", "Settings reset to default!")


        def change_appearance_mode_event(new_appearance_mode: str):
            set_appearance_mode(new_appearance_mode)
    
        def is_valid_directory(p):
            p = path.normpath(p)


            # Check if the path is a directory
            if path.isfile(p):
                return False, "The path is a file. Please provide a directory."

            # Check for Windows disallowed characters
            # We'll remove '/' and '\\' from the disallowed list because we're allowing them now.
            disallowed_chars = ['<', '>', '"', '|', '?', '*']
            for char in disallowed_chars:
                if char in p:
                    return False, f"Path contains a disallowed character: {char}"

            return True, "Path is valid."

        def select_directory():
            selected_dir = filedialog.askdirectory()
            if selected_dir:  # If a directory was selected
                self.filepath_entry.delete(0, END)
                self.filepath_entry.insert(0, selected_dir)

        def save_and_apply_settings(theme_var, filepath_entry):
            # Extract values from the StringVar and Entry
            load_config()
            theme_value = theme_var.get()
            filepath_value = filepath_entry.get()

            valid, message = is_valid_directory(filepath_value)
            if not valid:
                self.show_custom_messagebox("Error", message)
                return

            data = {
                "theme": theme_value,
                "download_path": filepath_value
            }

            # Save to JSON
            with open(config_file, 'w') as f:
                dump(data, f, indent=4)

            # Apply the appearance mode
            change_appearance_mode_event(theme_value)
            self.show_custom_messagebox("Success", "Settings saved!")

        self.current_page = "settings"
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()

        # Title Label
        label = CTkLabel(self.right_frame, text="Settings", font=("Arial", 32, "bold"), text_color=self.font_color, justify="center")
        label.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky="nsew")

        # Download Path Entry
        download_label = CTkLabel(self.right_frame, text="Download Path:", font=("Arial", 15, "bold"), text_color=self.font_color,)
        download_label.grid(row=1, column=0, padx=(10, 3), pady=10, sticky="w")

        self.filepath_entry = CTkEntry(self.right_frame, width=200, height=40)
        self.filepath_entry.grid(row=1, column=1, padx=(3,10), pady=10, sticky="w")

        self.select_folder_button = CTkButton(self.right_frame, text="Select", 
                                                  command=select_directory, width=50, height=40, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover)
        self.select_folder_button.grid(row=1, column=2, padx=(3,10), pady=10)

        # Load the existing download path from the config and set it to the entry
        self.filepath_entry.insert(0, config_data["download_path"])
        # Theme Selection
        theme_label = CTkLabel(self.right_frame, text="Theme:", font=("Arial", 18), text_color=self.font_color)
        theme_label.grid(row=2, column=0, padx=(10,3) , pady=10, sticky="nsew")

        self.theme_var = StringVar(value=config_data["theme"])  # Create a StringVar to hold the theme value
        self.theme_selector = CTkSegmentedButton(self.right_frame, values=["system","light", "dark"], 
                                                     variable=self.theme_var, width=350, height=40, selected_color=self.buttoncolor,selected_hover_color=self.buttoncolor_hover)
        self.theme_selector.grid(row=2, column=1, padx=(3,10), pady=10, sticky="w")

        # Save Button
        
        save_button = CTkButton(self.right_frame, text="Save", 
                            command=lambda: save_and_apply_settings(self.theme_var, self.filepath_entry), fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover)
        save_button.grid(row=3, column=0, columnspan=3, pady=(20, 0))
        reset_button = CTkButton(self.right_frame, text="Reset to Default", 
                             command=reset_to_default, fg_color=self.buttoncolor, hover_color=self.buttoncolor_hover,)
        reset_button.grid(row=4, column=0, columnspan=3, pady=(0,20))

        



    def show_about(self):
        self.current_page = "about"
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()

        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=0)  # Make it absolute
        self.right_frame.grid_rowconfigure(2, weight=0)  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(0, weight=1)  # Letting the column still expand horizontally
        # Padding for the entire frame
        self.right_frame['padx'] = 20
        self.right_frame['pady'] = 20
        # Set up the Scrollable Frame
        self.scrollable_frame = CTkScrollableFrame(self.right_frame, corner_radius=0, fg_color="transparent")
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

         # Title
        self.about_title_label = CTkLabel(self.scrollable_frame, text="About ForgeYT", font=("Arial", 40, "bold"), text_color=self.font_color, bg_color="transparent")
        self.about_title_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Origin
        self.origin_label = CTkLabel(self.scrollable_frame, text="Origin:", font=("Arial", 18, "bold"), text_color=self.font_color, bg_color="transparent")
        self.origin_label.grid(row=1, column=0, padx=10, pady=2, sticky="nsew")
        self.origin_content = CTkLabel(self.scrollable_frame, wraplength=350, text=("ForgeYT was born out of the need for a reliable YouTube to MP3 converter. "
                                                                    "With many of the popular YTMP3 websites being blocked at school, and others feeling dubious at best, "
                                                                    "there was a clear necessity for a trustworthy tool."), text_color=self.font_color, bg_color="transparent")
        self.origin_content.grid(row=2, column=0, padx=10, pady=2, sticky="nsew")

        # Initial Release
        self.release_label = CTkLabel(self.scrollable_frame, text="Initial Release:", font=("Arial", 18, "bold"), text_color=self.font_color, bg_color="transparent")
        self.release_label.grid(row=3, column=0, padx=10, pady=2, sticky="nsew")
        self.release_content = CTkLabel(self.scrollable_frame, wraplength=350, text=("The first iteration of ForgeYT was launched in February 2023. Beginning its journey as a Node.js CLI tool, it has undergone significant evolution to become the Python GUI application you see today."), text_color=self.font_color, bg_color="transparent")
        self.release_content.grid(row=4, column=0, padx=10, pady=2, sticky="nsew")

        # Challenges
        self.challenges_label = CTkLabel(self.scrollable_frame, text="Challenges:", font=("Arial", 18, "bold"), text_color=self.font_color, bg_color="transparent")
        self.challenges_label.grid(row=5, column=0, padx=10, pady=2, sticky="nsew")
        self.challenges_content = CTkLabel(self.scrollable_frame, wraplength=350, text=("Transitioning from Node.js to Python was no small feat. Integrating `yt-dlp` with Node.js's child-process presented unique challenges, but determination and innovation prevailed."), text_color=self.font_color, bg_color="transparent")
        self.challenges_content.grid(row=6, column=0, padx=10, pady=2, sticky="nsew")

        # Purpose & Usage
        self.purpose_label = CTkLabel(self.scrollable_frame, text="Purpose & Usage:", font=("Arial", 18, "bold"), text_color=self.font_color, bg_color="transparent")
        self.purpose_label.grid(row=7, column=0, padx=10, pady=2, sticky="nsew")
        self.purpose_content = CTkLabel(self.scrollable_frame, wraplength=350, text=("While ForgeYT was originally designed for use within a school environment, its versatility makes it apt for varied situations. Convert YouTube videos to audio with ease, regardless of where you are."), text_color=self.font_color, bg_color="transparent")
        self.purpose_content.grid(row=8, column=0, padx=10, pady=2, sticky="nsew")

        # acknowledgemnts
        self.ack_label = CTkLabel(self.scrollable_frame, text="Acknowledgments:", font=("Arial", 18, "bold"), text_color=self.font_color, bg_color="transparent")
        self.ack_label.grid(row=9, column=0, padx=10, pady=2, sticky="nsew")
        self.ack_content = CTkLabel(self.scrollable_frame, wraplength=350, text=("A heartfelt thank you to Mr. Z and DJ Stomp for their invaluable contributions. Additionally, a shout-out to the Python Discord community for their support."), text_color=self.font_color, bg_color="transparent")
        self.ack_content.grid(row=10, column=0, padx=10, pady=2, sticky="nsew")
        
        # Future
        self.ack_label = CTkLabel(self.scrollable_frame, text="Future:", font=("Arial", 18, "bold"), text_color=self.font_color, bg_color="transparent")
        self.ack_label.grid(row=11, column=0, padx=10, pady=2, sticky="nsew")
        self.ack_content = CTkLabel(self.scrollable_frame, wraplength=350, text=("ForgeYT stands proud at version 2.0. While this is likely its final form, the journey and impact it has had remain invaluable."), text_color=self.font_color, bg_color="transparent")
        self.ack_content.grid(row=12, column=0, padx=10, pady=2, sticky="nsew")

        self.version_label = CTkLabel(self.scrollable_frame, text=f"Current Version: {currentversion}",text_color=self.font_color, bg_color="transparent", font=("Arial", 10, "italic"))
        self.version_label.grid(row=13, column=0, padx=10, pady=10, sticky="nsew")

    def insert_text_in_chunks(self, widget, text, chunk_size=50000):
        """
        Insert text into a Text widget in chunks to avoid OverflowError.
        """
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            widget.insert(END, chunk)

    def write(self, s, from_queue=False):
        # Append a newline if the message is from the queue and doesn't have one
        if from_queue and not s.endswith('\n'):
            s += '\n'
        self.output_buffer += s
        if self.console_output:
            self.console_output.configure(state=NORMAL)  # Enable widget for editing
            # Check for the '\r' character to overwrite the current line
            if '\r' in s:
                # Move the cursor to the start of the current line
                self.cursor_position = self.console_output.index(END + "-1 lines linestart")
                # Delete the entire current line
                self.console_output.delete(self.cursor_position, END + "-1 lines lineend")
                # Remove the '\r' from the string
                s = s.replace('\r', '')
                # Insert the modified string at the current cursor position
                self.console_output.insert(self.cursor_position, s)
            else:
                # If no '\r', just append to the end
                self.console_output.insert(END, s)
            # Update the cursor position
            self.cursor_position = self.console_output.index(END)
            # Make sure the view is always showing the most recent data
            self.console_output.yview(END)
            self.console_output.configure(state=DISABLED)  # Disable widget after editing

    def display_buffer(self):
        lines = self.output_buffer.split('\n')
        processed_lines = []
        for line in lines:
            if '\r' in line:
                line = line.split('\r')[-1]
            processed_lines.append(line)
        final_output = '\n'.join(processed_lines)
        self.console_output.configure(state=NORMAL)
        self.console_output.delete(1.0, END)
        self.console_output.insert(END, final_output)
        self.console_output.configure(state=DISABLED)

    def show_console(self):
        self.current_page = "console"
        # Hide other widgets in the right frame
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()
        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=0)  # Make it absolute
        self.right_frame.grid_rowconfigure(2, weight=0)  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(0, weight=1)  # Letting the column still expand horizontally
        # Display the buffered output in the console_output widget
        self.display_buffer()
        self.right_frame.grid(sticky='nsew')
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        # Grid the console_output to take full space in its grid cell with external padding
        self.console_output.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        # Initialize the cursor position to the end of the console_output widget
        self.cursor_position = self.console_output.index(END)

    def limit_entry_size(self, *args):
        value = self.entry_var.get()
        if len(value) > 40:
            self.entry_var.set(value[:40])

root = CTk(fg_color=('#bef8ec', '#031b16'))
app = App(root)
root.mainloop()
