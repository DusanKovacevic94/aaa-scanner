import tkinter as tk
from tkinter import messagebox
import threading
import time
import mss
import mss.tools
import requests
import keyboard
import os
import io
from PIL import Image

import configparser

API_URL = "http://localhost:8000/match"
TRIGGER_KEY = "F9" # Default key

# Load Config
config = configparser.ConfigParser()
config.read("config.ini")
CAPTURE_WIDTH = int(config.get("Scanner", "capture_width", fallback=400))
CAPTURE_HEIGHT = int(config.get("Scanner", "capture_height", fallback=60))

class ScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AAA Scanner")
        self.root.geometry("300x250")

        self.is_running = False
        
        # UI Elements
        tk.Label(root, text="Discord ID:").pack(pady=5)
        self.discord_id_entry = tk.Entry(root)
        self.discord_id_entry.pack(pady=5)

        tk.Label(root, text=f"Press {TRIGGER_KEY} to Scan & Join").pack(pady=10)

        self.status_label = tk.Label(root, text="Status: Ready", fg="blue")
        self.status_label.pack(pady=10)

        self.log_text = tk.Text(root, height=5, width=35, state='disabled')
        self.log_text.pack(pady=5)

        # Load saved ID
        if os.path.exists("discord_id.txt"):
            with open("discord_id.txt", "r") as f:
                self.discord_id_entry.insert(0, f.read().strip())

        # Start Key Listener
        self.start_listener()

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_listener(self):
        # We use a background thread to listen for the key to avoid blocking UI
        # However, 'keyboard' library hooks are usually non-blocking or can be used with add_hotkey
        try:
            keyboard.add_hotkey(TRIGGER_KEY, self.on_trigger)
            self.log(f"Listening for {TRIGGER_KEY}...")
        except Exception as e:
            self.log(f"Error hooking key: {e}")

    def on_trigger(self):
        # This runs in a separate thread usually when invoked by keyboard
        discord_id = self.discord_id_entry.get().strip()
        if not discord_id:
            self.root.after(0, lambda: messagebox.showerror("Error", "Please enter Discord ID"))
            return

        # Save ID
        with open("discord_id.txt", "w") as f:
            f.write(discord_id)

        self.root.after(0, lambda: self.status_label.config(text="Scanning...", fg="orange"))
        self.capture_and_send(discord_id)

    def capture_and_send(self, discord_id):
        try:
            with mss.mss() as sct:
                # Monitor 1 usually.
                monitor = sct.monitors[1]
                width = monitor["width"]
                height = monitor["height"]
                
                # Define capture area
                capture_width = CAPTURE_WIDTH
                capture_height = CAPTURE_HEIGHT
                
                monitor_region = {
                    "top": monitor["top"] + height - capture_height,
                    "left": monitor["left"] + width - capture_width,
                    "width": capture_width,
                    "height": capture_height,
                    "mon": 1,
                }

                sct_img = sct.grab(monitor_region)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                # Send to Bot
                files = {'file': ('screenshot.png', img_byte_arr, 'image/png')}
                data = {'discord_id': discord_id}
                
                self.root.after(0, lambda: self.log("Sending to bot..."))
                
                response = requests.post(API_URL, data=data, files=files)
                
                if response.status_code == 200:
                    self.root.after(0, lambda: self.status_label.config(text="Success!", fg="green"))
                    self.root.after(0, lambda: self.log("Match request sent."))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="Failed", fg="red"))
                    self.root.after(0, lambda: self.log(f"Error: {response.text}"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error: {e}"))
            self.root.after(0, lambda: self.status_label.config(text="Error", fg="red"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ScannerApp(root)
    root.mainloop()
