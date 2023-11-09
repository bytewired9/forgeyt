from customtkinter import CTkToplevel, CTkLabel, CTkButton
class CustomMessageBox:
    _instance = None  # Class variable to keep track of the current instance

    def __init__(self, root, title, message, buttoncolor, buttoncolor_hover):
        if CustomMessageBox._instance:  # Check if an instance already exists
            CustomMessageBox._instance.top.destroy()  # Destroy the existing instance

        self.top = CTkToplevel(root)
        self.top.title(title)
        self.top.resizable(False, False)
        CustomMessageBox._instance = self  # Update the class variable

        self.label = CTkLabel(self.top, text=message, wraplength=250)
        self.label.pack(padx=10, pady=10)

        self.button = CTkButton(
            self.top,
            text="OK",
            command=self.destroy_messagebox,
            fg_color=buttoncolor,
            hover_color=buttoncolor_hover,
            width=80,
        )
        self.button.pack(pady=10)

        # Make the messagebox transient to the main window
        self.top.transient(root)
        # Ensure that it always stays on top
        self.top.attributes("-topmost", True)

        self.top.update_idletasks()  # Update the GUI tasks

        # Calculate the width and height based on individual widget sizes
        window_width = max(
            self.top.winfo_width(), self.label.winfo_width() + 20
        )  # 20 to accommodate padding
        # Add up the heights of individual widgets with padding
        window_height = (
            self.label.winfo_height() + self.button.winfo_height() + 40
        )  # 40 to accommodate padding

        # Calculate the center position of the main window
        pos_x = root.winfo_x() + (root.winfo_width() // 2)
        pos_y = root.winfo_y() + (root.winfo_height() // 2)

        # Adjust so that the messagebox is centered on the main window
        center_x = pos_x - (window_width // 2)
        center_y = pos_y - (window_height // 2)

        # Set the new position and dimensions
        self.top.geometry(
            "%dx%d+%d+%d" % (window_width, window_height, center_x, center_y)
        )

    def destroy_messagebox(self):
        CustomMessageBox._instance = None  # Clear the class variable
        self.top.destroy()