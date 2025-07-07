import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

SCRIPT = "start_menu.py"  # Change to your Tkinter script

class ReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
        self.process = subprocess.Popen([sys.executable, SCRIPT])

    def on_modified(self, event):
        if event.src_path.endswith(SCRIPT):
            print(f"{SCRIPT} changed, reloading...")
            self.start_process()

if __name__ == "__main__":
    event_handler = ReloadHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(os.path.abspath(SCRIPT)) or '.', recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    if event_handler.process:
        event_handler.process.terminate()