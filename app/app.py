"""ForgeYT UI Section"""
from os import path
from urllib.parse import urlparse
from threading import Thread, Event
from json import dump
from queue import Queue, Empty
from tkinter import filedialog, StringVar
from ctypes import windll
from webbrowser import open as webopen
import sys
from customtkinter import (
    CTkScrollableFrame,
    NORMAL,
    CTkComboBox,
    CTkSegmentedButton,
    CTkEntry,
    CTkImage,
    END,
    CTkLabel,
    CTkButton,
    CTkFrame,
    set_appearance_mode,
    CTkTextbox,
    WORD,
    CTkCheckBox,
    DISABLED,
)
from PIL import Image
import requests
from utils import (
    download,
    windowTheme,
    CURRENT_VERSION,
    config_file,
    DEFAULT_SETTINGS,
    load_config,
    resource_path
    )
from vars import filetypes
from .messagebox import CustomMessageBox

class App(CTkFrame):
    """App class that includes all the fun spaghetti that
    I wont fix because I cant read it :P"""
    # print("app class started")
    def flush(self):
        pass

    def __init__(self, root):
        print("initializing...")
        super().__init__(root)
        self.root = root
        # print("getting DPI")
        # print("setting font color")
        self.font_color = ("black", "white")
        # print("setting colors")
        self.background_color1 = ("#fafefe", "#04251e")
        self.background_color2 = ("#f3d3da", "#031b16")
        self.buttoncolor = ("#d21941", "#c83232")
        self.buttoncolor_hover = ("#841029", "#970222")
        def get_system_dpi():
            hdc = windll.user32.GetDC(0)
            dpi = windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 is LOGPIXELSX
            windll.user32.ReleaseDC(0, hdc)
            return dpi / 96  # The base value is 96 DPI which is 100% scaling
        def get_scaling_factor(dpi_scaling):
            if dpi_scaling <= 1.0:  # 100% scaling or less
                return 0.8
            elif dpi_scaling <= 1.25:  # 125% scaling
                return 1.0
            elif dpi_scaling <= 1.5:  # 150% scaling
                return 1.2
            else:  # 175% scaling or more
                return 1.4
        dpi_scaling = get_system_dpi()
        scaling_factor = get_scaling_factor(dpi_scaling)
        # print(f"Chosen Scaling Factor: {scaling_factor}")  # Debug statement
        # print("setting geometry")
        self.root.minsize(600, 450)

        self.root.grid_columnconfigure(
            0, minsize=100*scaling_factor
        )  # First column fixed at 100 pixels
        self.root.grid_columnconfigure(
            1, minsize=550*scaling_factor
        )  # Second column fixed at 500 pixels
        self.root.grid_rowconfigure(0, weight=1)  # Makes the row 0 expand vertically
        # print("setting left_frame")
        self.left_frame = CTkFrame(self.root, fg_color=self.background_color2)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        # print("setting right frame")
        self.right_frame = CTkFrame(root, fg_color=self.background_color1)
        self.right_frame.grid(
            row=0, column=1, rowspan=4, sticky="nsew", padx=10, pady=10)
        self.canvas_img = None
        # print("setting resizability")
        self.root.resizable(False, False)
        # print("setting title")
        self.root.title("ForgeYT")
        # print("setting current_page")
        self.current_page = "none"
        # print("setting download_thread")
        self.download_thread = None  # To keep track of download thread
        # print("setting url_of_the_profile_page")
        self.url_of_the_profile_page = None
        # print("setting console output")
        self.console_output = CTkTextbox(
            self.right_frame, wrap=WORD, padx=20, pady=20, state=DISABLED
        )
        self.console_output.grid_forget()
        self.cursor_position = "1.0"
        # print("loading globals...")
        globals()
        # print("setting appearance mode")
        set_appearance_mode(windowTheme)
        # print("setting output buffer")
        self.output_buffer = ""
        self.open_explorer = StringVar(value="True")
        # print("setting up UI")
        self.setup_ui()
        # print("setting up newline pos")
        self.last_newline_position = END
        # print("setting queue")
        self.queue = Queue()
        # print("stop threads")
        self.stop_threads = Event()
        # print("setting close app protocol")
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        # print("checking queue")
        self.check_queue()
        # print("setting loading label")
        self.loading_label = CTkLabel(
            self.right_frame,
            text="Processing...",
            text_color=self.font_color,
            bg_color="transparent",
        )
        self.loading_label.grid(pady=40)
        self.loading_label.grid_forget()
        # print("setting start button")
        self.start_image = CTkImage(
            light_image=Image.open(resource_path("assets/download.png")),
            dark_image=Image.open(resource_path("assets/download_dark.png")),
            size=(30, 30),
        )
        self.start_button = CTkButton(
            self.right_frame,
            image=self.start_image,
            text="",
            command=self.start_downloading,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
            height=50,
            width=120,
        )
        self.start_button.grid(pady=(30,0))
        self.start_button.grid_forget()
        # print("setting stop event")
        self.stop_event = Event()
        # print("setting scalable_elements")
        self.scalable_elements = {
            "title_label": None,  # We'll store the actual label here later
            "url_label": None,
            "start_button": None,
        }
        # print("setting current font size")
        self.current_font_size = (
            16  # This would be the initial font size for your elements.
        )
        # print("setting dropdown menu")
        self.dropdown_options = [key.upper() for key in filetypes]
        self.dropdown_menu = CTkComboBox(
            self.right_frame, values=self.dropdown_options, corner_radius=6
        )
        # print("setting profile entry")
        self.profile_entry = CTkEntry(self.right_frame, width=30)
        self.profile_entry.grid(row=2, column=0, pady=(5, 5), padx=60, sticky="ew")
        self.profile_entry.grid_forget()  # Initially hide it if the home is not the default screen
        # print("showing home")
        def close_console():
            windll.user32.ShowWindow(windll.kernel32.GetConsoleWindow(), 0)
        if getattr(sys, 'frozen', False):
            self.show_home()
            close_console()
            # print("setting icon path")
            icon_path = resource_path("assets/ForgeYT.ico")
            self.root.iconbitmap(default=icon_path)
        else:
            self.show_home()
        self.after_id = None
        self.original_stdout = sys.stdout
        sys.stdout = self

    def close_app(self):
        # Signal all threads to stop
        self.stop_threads.set()

        # If there are other cleanup tasks, perform them here
        # return stdout to OG
        sys.stdout = self.original_stdout
        # Close the window
        self.root.quit()
        self.root.destroy()

    def show_custom_messagebox(self, title="Message", message="Something happened!"):
        CustomMessageBox(self.root, title, message, self.buttoncolor, self.buttoncolor_hover)

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
        self.download_thread = Thread(
            target=download, args=(url, filetype, self.queue, self.open_explorer, self)
        )
        self.download_thread.start()

        # Hide the start button and show the loading label
        self.start_button.grid_forget()
        self.loading_label.grid(pady=(40,0))

    def cleanup_after_thread(self):

        # Hide the loading_label if it's present
        self.loading_label.grid_forget()
        self.profile_entry.delete(0, END)
        self.dropdown_menu.set("MP4")

        # Check if start_button is currently displayed (gridded)
        if self.current_page == "home" and not self.start_button.grid_info():
            self.start_button.grid(pady=(30,0))

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
        self.forgeyt_image = CTkImage(
            Image.open(resource_path("assets/ForgeYT.png")), size=(120, 120)
        )
        self.home_image = CTkImage(
            light_image=Image.open(resource_path("assets/Home.png")),
            dark_image=Image.open(resource_path("assets/Home_dark.png")),
            size=(button_height - 20, button_height - 20),
        )
        self.settings_image = CTkImage(
            light_image=Image.open(resource_path("assets/Settings.png")),
            dark_image=Image.open(resource_path("assets/Settings_dark.png")),
            size=(button_height - 20, button_height - 20),
        )
        self.about_image = CTkImage(
            light_image=Image.open(resource_path("assets/About.png")),
            dark_image=Image.open(resource_path("assets/About_dark.png")),
            size=(button_height - 20, button_height - 20),
        )
        self.console_image = CTkImage(
            light_image=Image.open(resource_path("assets/Console.png")),
            dark_image=Image.open(resource_path("assets/Console_dark.png")),
            size=(button_height - 20, button_height - 20),
        )
        self.image_label = CTkLabel(self.left_frame, image=self.forgeyt_image, text="")
        self.image_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.image_label_label = CTkLabel(
            self.left_frame,
            text="ForgeYT",
            font=("Arial", 30, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        self.image_label_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(1, 10))
        self.home_button = CTkButton(
            self.left_frame,
            image=self.home_image,
            text="",
            command=self.show_home,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
            height=button_height,
        )
        self.home_button.grid(
            row=2, column=0, sticky="ew", padx=10, pady=button_padding_y
        )
        self.settings_button = CTkButton(
            self.left_frame,
            image=self.settings_image,
            text="",
            command=self.show_settings,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
            height=button_height,
        )
        self.settings_button.grid(
            row=3, column=0, sticky="ew", padx=10, pady=button_padding_y
        )
        self.about_button = CTkButton(
            self.left_frame,
            image=self.about_image,
            text="",
            command=self.show_about,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
            height=button_height,
        )
        self.about_button.grid(
            row=4, column=0, sticky="ew", padx=10, pady=button_padding_y
        )
        self.console_button = CTkButton(
            self.left_frame,
            image=self.console_image,
            text="",
            command=self.show_console,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
            height=button_height,
        )
        self.console_button.grid(
            row=5, column=0, sticky="ew", padx=10, pady=button_padding_y
        )

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


    def open_browser(self):
        webopen("https://github.com/ForgedCore8/forgeyt/releases/latest")

    def get_latest_release(self):
        url = "https://api.github.com/repos/ForgedCore8/forgeyt/releases/latest"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get('tag_name')
        else:
            return None
    def is_newer_version(self, current_version, latest_version):
        current = [int(x) for x in current_version.split('.')]
        latest = [int(x) for x in latest_version.split('.')]
        return latest > current

    def show_home(self):

        self.current_page = "home"
        # Clear existing widgets
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()
        # Configure rows and columns for scalability
        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=0)  # Make it absolute
        self.right_frame.grid_rowconfigure(
            2, weight=0
        )  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(
            0, weight=1
        )  # Letting the column still expand horizontally
        # Padding for the entire frame
        self.right_frame["padx"] = 20
        self.right_frame["pady"] = 20
        # Title Label
        self.scalable_elements["title_label"] = CTkLabel(
            self.right_frame,
            text="ForgeYT",
            font=("Arial", 50, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        self.scalable_elements["title_label"].grid(
            row=0, column=0, pady=50, sticky="nsew"
        )
        # Profile URL Input Label
        self.scalable_elements["url_label"] = CTkLabel(
            self.right_frame,
            text="Enter Video URL",
            font=("Arial", 20),
            text_color=self.font_color,
            bg_color="transparent",
        )
        self.scalable_elements["url_label"].grid(
            row=1, column=0, pady=(0, 10), sticky="nsew"
        )  # Adjust the top padding to be more than the bottom padding

        # Entry Box for Profile URL
        self.profile_entry.grid(
            row=2, column=0, pady=(5, 5), padx=60, sticky="ew"
        )  # Adjust the bottom padding to be more than the top padding
        # Check if a download is in progress; Display appropriate button
        # Dropdown Menu (Combobox) below the Entry Box
        self.dropdown_label = CTkLabel(
            self.right_frame,
            text="Select File Type",
            font=("Arial", 20),
            text_color=self.font_color,
            bg_color="transparent",
        )
        self.dropdown_label.grid(row=3, column=0, pady=(5, 5), sticky="nsew")
        self.dropdown_menu.grid(
            row=4, column=0, pady=5, padx=60, sticky="ew"
        )  # Adjust padding and placement accordingly
        self.open_explorerbox = CTkCheckBox(self.right_frame, text="Open in File Explorer",
                                     variable=self.open_explorer, onvalue="True", offvalue="False")
        self.open_explorerbox.grid(
            row=5, column=0, pady=5, padx=60, sticky="ew"
        )  # Adjust padding and placement accordingly
        if self.download_thread and self.download_thread.is_alive():
            self.loading_label.grid(row=6, column=0, pady=(40,0))
        else:
            self.start_button.grid(row=6, column=0, pady=(30,0))
        latest_version = self.get_latest_release()
        if latest_version and self.is_newer_version(CURRENT_VERSION, latest_version):
            self.update_button = CTkButton(
                self.right_frame,
                text="New version available!",
                command=self.open_browser
            )
            self.update_button.grid(row=7, column=0, pady=5)  # Adjust the grid position accordingly

    def show_settings(self):
        config_data = load_config()
        #download_path = config_data["download_path"]
        self.right_frame.grid_columnconfigure(0, weight=1)
        #windowTheme = config_data["theme"]
        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=3)  # Make it absolute
        # self.right_frame.grid_rowconfigure(2, weight=0)
        self.right_frame.grid_columnconfigure(
            0, weight=1
        )  # Letting the column still expand horizontally

        def reset_to_default():
            # Update the config file
            with open(config_file, "w", encoding="utf-8") as f:
                dump(DEFAULT_SETTINGS, f, indent=4)

            # Update the GUI elements
            filepath_entry.delete(0, END)
            filepath_entry.insert(0, DEFAULT_SETTINGS["download_path"])
            theme_var.set(DEFAULT_SETTINGS["theme"])
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
            disallowed_chars = ["<", ">", '"', "|", "?", "*"]
            for char in disallowed_chars:
                if char in p:
                    return False, f"Path contains a disallowed character: {char}"

            return True, "Path is valid."

        def select_directory():
            selected_dir = filedialog.askdirectory()
            if selected_dir:  # If a directory was selected
                filepath_entry.delete(0, END)
                filepath_entry.insert(0, selected_dir)

        def save_and_apply_settings(theme_var, filepath_entry):
            # Extract values from the StringVar and Entry
            load_config()
            theme_value = theme_var.get()
            filepath_value = filepath_entry.get()

            valid, message = is_valid_directory(filepath_value)
            if not valid:
                self.show_custom_messagebox("Error", message)
                return

            data = {"theme": theme_value, "download_path": filepath_value}

            # Save to JSON
            with open(config_file, "w", encoding="utf-8") as f:
                dump(data, f, indent=4)

            # Apply the appearance mode
            change_appearance_mode_event(theme_value)
            self.show_custom_messagebox("Success", "Settings saved!")

        self.current_page = "settings"
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()

        # Title Label
        label = CTkLabel(
            self.right_frame,
            text="Settings",
            font=("Arial", 32, "bold"),
            text_color=self.font_color,
            justify="center",
        )
        label.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky="nsew")

        # Download Path Entry
        download_label = CTkLabel(
            self.right_frame,
            text="Download Path:",
            font=("Arial", 15, "bold"),
            text_color=self.font_color,
        )
        download_label.grid(row=1, column=0, padx=(10, 3), pady=10, sticky="w")

        filepath_entry = CTkEntry(self.right_frame, width=200, height=40)
        filepath_entry.grid(row=1, column=1, padx=(3, 10), pady=10, sticky="w")

        select_folder_button = CTkButton(
            self.right_frame,
            text="Select",
            command=select_directory,
            width=50,
            height=40,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
        )
        select_folder_button.grid(row=1, column=2, padx=(3, 10), pady=10)

        # Load the existing download path from the config and set it to the entry
        filepath_entry.insert(0, config_data["download_path"])
        # Theme Selection
        theme_label = CTkLabel(
            self.right_frame,
            text="Theme:",
            font=("Arial", 18),
            text_color=self.font_color,
        )
        theme_label.grid(row=2, column=0, padx=(10, 3), pady=10, sticky="nsew")

        theme_var = StringVar(
            value=config_data["theme"]
        )  # Create a StringVar to hold the theme value
        theme_selector = CTkSegmentedButton(
            self.right_frame,
            values=["system", "light", "dark"],
            variable=theme_var,
            width=350,
            height=40,
            selected_color=self.buttoncolor,
            selected_hover_color=self.buttoncolor_hover,
        )
        theme_selector.grid(row=2, column=1, padx=(3, 10), pady=10, sticky="w")

        # Save Button

        save_button = CTkButton(
            self.right_frame,
            text="Save",
            command=lambda: save_and_apply_settings(
                theme_var, filepath_entry
            ),
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
        )
        save_button.grid(row=3, column=0, columnspan=3, pady=(20, 0))
        reset_button = CTkButton(
            self.right_frame,
            text="Reset to Default",
            command=reset_to_default,
            fg_color=self.buttoncolor,
            hover_color=self.buttoncolor_hover,
        )
        reset_button.grid(row=4, column=0, columnspan=3, pady=(0, 20))

    def show_about(self):
        self.current_page = "about"
        for widget in self.right_frame.winfo_children():
            widget.grid_forget()

        for i in range(4):  # We have 4 rows
            self.right_frame.grid_rowconfigure(i, weight=0)  # Make it absolute
        self.right_frame.grid_rowconfigure(
            2, weight=0
        )  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(
            0, weight=1
        )  # Letting the column still expand horizontally
        # Padding for the entire frame
        self.right_frame["padx"] = 20
        self.right_frame["pady"] = 20
        # Set up the Scrollable Frame
        scrollable_frame = CTkScrollableFrame(
            self.right_frame, corner_radius=0, fg_color="transparent"
        )
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Title
        about_title_label = CTkLabel(
            scrollable_frame,
            text="About ForgeYT",
            font=("Arial", 40, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        about_title_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Origin
        origin_label = CTkLabel(
            scrollable_frame,
            text="Origin:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        origin_label.grid(row=1, column=0, padx=10, pady=2, sticky="nsew")
        origin_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "ForgeYT was born out of the need for a reliable YouTube to MP3 converter. "
                "With many of the popular YTMP3 websites being blocked"+
                " at school, and others feeling dubious at best, "
                "there was a clear necessity for a trustworthy tool."
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        origin_content.grid(row=2, column=0, padx=10, pady=2, sticky="nsew")

        # Initial Release
        release_label = CTkLabel(
            scrollable_frame,
            text="Initial Release:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        release_label.grid(row=3, column=0, padx=10, pady=2, sticky="nsew")
        release_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "The first iteration of ForgeYT was launched in February 2023."+
                " Beginning its journey as a Node.js CLI tool, it has undergone"+
                " significant evolution to become the Python GUI application you see today."
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        release_content.grid(row=4, column=0, padx=10, pady=2, sticky="nsew")

        # Challenges
        challenges_label = CTkLabel(
            scrollable_frame,
            text="Challenges:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        challenges_label.grid(row=5, column=0, padx=10, pady=2, sticky="nsew")
        challenges_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "Transitioning from Node.js to Python was no small feat."+
                " Integrating `yt-dlp` with Node.js's child-process presented "+
                "unique challenges, but determination and innovation prevailed."
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        challenges_content.grid(row=6, column=0, padx=10, pady=2, sticky="nsew")

        # Purpose & Usage
        purpose_label = CTkLabel(
            scrollable_frame,
            text="Purpose & Usage:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        purpose_label.grid(row=7, column=0, padx=10, pady=2, sticky="nsew")
        purpose_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "While ForgeYT was originally designed for use within a school" +
                " environment, its versatility makes it apt for varied situations." +
                " Convert YouTube videos to audio with ease, regardless of where you are."
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        purpose_content.grid(row=8, column=0, padx=10, pady=2, sticky="nsew")

        # acknowledgemnts
        ack_label = CTkLabel(
            scrollable_frame,
            text="Acknowledgments:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        ack_label.grid(row=9, column=0, padx=10, pady=2, sticky="nsew")
        ack_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "A heartfelt thank you to Mr. Z and DJ Stomp for their"+
                " invaluable contributions. Additionally, a shout-out to " +
                "the Python Discord community for their support."
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        ack_content.grid(row=10, column=0, padx=10, pady=2, sticky="nsew")

        # Future
        ack_label = CTkLabel(
            scrollable_frame,
            text="Future:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        ack_label.grid(row=11, column=0, padx=10, pady=2, sticky="nsew")
        ack_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "ForgeYT stands proud at version 2.0. While this is " +
                "likely its final form, the journey and impact it has "+
                "had remain invaluable."
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        ack_content.grid(row=12, column=0, padx=10, pady=2, sticky="nsew")
        whatsnew_label = ack_label = CTkLabel(
            scrollable_frame,
            text="Whats New?:",
            font=("Arial", 18, "bold"),
            text_color=self.font_color,
            bg_color="transparent",
        )
        whatsnew_label.grid(row=13, column=0, padx=10, pady=2, sticky="nsew")
        whatsnew_content = CTkLabel(
            scrollable_frame,
            wraplength=350,
            text=(
                "- Fixed a problem where file Extensions were"+ 
                "duplicated at the end of file name\n" +
                "- Fixed an issue with Starting Format being" +
                " reset to MP3 while the default was MP4\n" +
                "- Added \"Open Explorer\" Checkbox in the event"+
                " that the user does not want to open explorer each time\n" +
                "- Added \"Whats New?\" Section to the About Page\n" +
                "- Additional Optimizations"
            ),
            text_color=self.font_color,
            bg_color="transparent",
        )
        whatsnew_content.grid(row=14, column=0, padx=10, pady=2, sticky="nsew")
        version_label = CTkLabel(
            scrollable_frame,
            text=f"Current Version: {CURRENT_VERSION}",
            text_color=self.font_color,
            bg_color="transparent",
            font=("Arial", 10, "italic"),
        )
        version_label.grid(row=15, column=0, padx=10, pady=10, sticky="nsew")

    def insert_text_in_chunks(self, widget, text, chunk_size=50000):
        """
        Insert text into a Text widget in chunks to avoid OverflowError.
        """
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            widget.insert(END, chunk)

    def write(self, s, from_queue=False):
        # Append a newline if the message is from the queue and doesn't have one
        if from_queue and not s.endswith("\n"):
            s += "\n"
        self.output_buffer += s
        if self.console_output:
            self.console_output.configure(state=NORMAL)  # Enable widget for editing
            # Check for the '\r' character to overwrite the current line
            if "\r" in s:
                # Move the cursor to the start of the current line
                self.cursor_position = self.console_output.index(
                    END + "-1 lines linestart"
                )
                # Delete the entire current line
                self.console_output.delete(
                    self.cursor_position, END + "-1 lines lineend"
                )
                # Remove the '\r' from the string
                s = s.replace("\r", "")
                # Insert the modified string at the current cursor position
                self.console_output.insert(self.cursor_position, s)
            else:
                # If no '\r', just append to the end
                self.console_output.insert(END, s)
            # Update the cursor position
            self.cursor_position = self.console_output.index(END)
            # Make sure the view is always showing the most recent data
            self.console_output.yview(END)
            self.console_output.configure(
                state=DISABLED
            )  # Disable widget after editing

    def display_buffer(self):
        lines = self.output_buffer.split("\n")
        processed_lines = []
        for line in lines:
            if "\r" in line:
                line = line.split("\r")[-1]
            processed_lines.append(line)
        final_output = "\n".join(processed_lines)
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
        self.right_frame.grid_rowconfigure(
            2, weight=0
        )  # If you want the row of the entry box to expand with the window
        self.right_frame.grid_columnconfigure(
            0, weight=1
        )  # Letting the column still expand horizontally
        # Display the buffered output in the console_output widget
        self.display_buffer()
        self.right_frame.grid(sticky="nsew")
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        # Grid the console_output to take full space in its grid cell with external padding
        self.console_output.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        # Initialize the cursor position to the end of the console_output widget
        self.cursor_position = self.console_output.index(END)

print("starting app")
