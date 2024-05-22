"""Initiatior for app"""
from customtkinter import CTk
from .app import App

def start_app():
    """Letsa go"""
    root = CTk(fg_color=("#f3d3da", "#031b16"))
    App(root)
    root.mainloop()
