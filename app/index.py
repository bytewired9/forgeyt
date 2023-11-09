from .app import App
from customtkinter import CTk
def start_app():
    root = CTk(fg_color=("#f3d3da", "#031b16"))
    app = App(root)
    root.mainloop()