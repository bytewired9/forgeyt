import time
from os import utime
def hooker (d):
    if d['status'] == 'finished':
        file_path = d['filename']
        times = (time.time(), time.time())
        utime(file_path, times)
        print(f"Downloaded and timestamp updated: {file_path}")