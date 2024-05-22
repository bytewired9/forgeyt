"""Initiating functions"""
from os import path
from utils import add_pwd_to_path
from app import start_app

add_pwd_to_path(path.dirname(path.abspath(__file__)))
start_app()
