import hashlib
import os
import json
import time
import threading
from tkinter import Tk, filedialog, messagebox, Button, Label
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants
HASH_RECORD = 'hash_records.json'

# Function to calculate SHA-256 hash of a file
def calculate_hash(file_path):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None

# Function to scan all files in the selected directory and calculate their hashes
def scan_directory(directory):
    file_hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, directory)
            hash_val = calculate_hash(path)
            if hash_val:
                file_hashes[rel_path] = hash_val
    return file_hashes

# Save current hash records to file
def save_hashes(data):
    with open(HASH_RECORD, 'w') as f:
        json.dump(data, f, indent=4)

# Load previous hash records
def load_hashes():
    if not os.path.exists(HASH_RECORD):
        return {}
    with open(HASH_RECORD, 'r') as f:
        return json.load(f)

# Compare old and new hash values
def compare_hashes(old, new):
    added, removed, changed = [], [], []

    for f in new:
        if f not in old:
            added.append(f)
        elif new[f] != old[f]:
            changed.append(f)
    for f in old:
        if f not in new:
            removed.append(f)

    return added, removed, changed

# Watchdog event handler for detecting changes
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory):
        self.directory = directory

    def on_any_event(self, event):
        new_hashes = scan_directory(self.directory)
        old_hashes = load_hashes()
        added, removed, changed = compare_hashes(old_hashes, new_hashes)

        if added or removed or changed:
            message = ""
            if added:
                message += f"🟢 Added:\n  " + "\n  ".join(added) + "\n"
            if removed:
                message += f"🔴 Removed:\n  " + "\n  ".join(removed) + "\n"
            if changed:
                message += f"🟡 Modified:\n  " + "\n  ".join(changed) + "\n"

            messagebox.showwarning("File Change Detected!", message)
            save_hashes(new_hashes)

# GUI start monitoring button
def start_monitoring():
    folder = filedialog.askdirectory(title="Select Folder to Monitor")
    if not folder:
        return

    messagebox.showinfo("Monitoring Started", f"Monitoring folder:\n{folder}")
    save_hashes(scan_directory(folder))  # Save initial state

    handler = FileChangeHandler(folder)
    observer = Observer()
    observer.schedule(handler, folder, recursive=True)
    observer.start()

    # Keep watchdog running in a separate thread
    def keep_running():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    threading.Thread(target=keep_running, daemon=True).start()

# Tkinter GUI setup
root = Tk()
root.title("🔐 File Integrity Checker")
root.geometry("400x220")
root.resizable(False, False)

Label(root, text="File Integrity Checker", font=("Arial", 16, "bold")).pack(pady=20)
Button(root, text="📁 Select Folder & Start Monitoring", font=("Arial", 12),
       command=start_monitoring, width=30, height=2).pack()

Label(root, text="Made with ❤️ in Python", font=("Arial", 10)).pack(side="bottom", pady=10)

root.mainloop()
