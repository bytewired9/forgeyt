
from utils import add_pwd_to_path
from os import path, getenv, makedirs, remove
from app import start_app
def load_modules():
    global requests, sys, remove, urlparse, Thread, Event, load, JSONDecodeError, dump, Queue, Empty, filedialog, StringVar, pygfont, run, path, getenv, makedirs, pyi_splash
    import sys
    from urllib.parse import urlparse
    from threading import Thread, Event
    from json import load, JSONDecodeError, dump
    from queue import Queue, Empty
    from tkinter import filedialog, StringVar
    from pyglet import font as pygfont
    from subprocess import run
    import requests

# ===================================== #
# =========  Module Imports  ========== #
# ===================================== #

add_pwd_to_path(path.dirname(path.abspath(__file__)))
start_app()




# ===========  Request Prompts  ===========




