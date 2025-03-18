#!/usr/bin/env python3
import os
import sys
import time
import logging
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Path to watch for changes
path = '.'
# Command to run your app
run_command = ['python3', 'main.py']

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_app()
        self.last_modified = time.time()

    def restart_app(self):
        if self.process:
            logging.info("Stopping GTK application...")
            self.process.terminate()
            self.process.wait()

        logging.info("Starting GTK application...")
        self.process = subprocess.Popen(run_command)

    def on_modified(self, event):
        # Avoid duplicate events (some editors trigger multiple events)
        if time.time() - self.last_modified < 0.5:
            return

        if event.is_directory:
            return

        # Only restart for Python files
        if event.src_path.endswith('.py'):
            logging.info(f"Change detected: {event.src_path}")
            self.last_modified = time.time()
            self.restart_app()

if __name__ == "__main__":
    logging.info(f"Watching for changes in {os.path.abspath(path)}")
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()

    observer.join()