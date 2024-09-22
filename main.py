import json
import time
import threading
import keyboard
import sys
import win32api
import win32con
from ctypes import WinDLL
import numpy as np
from mss import mss as mss_module
from flask import Flask, render_template, request
import os
import string
import random

app = Flask(__name__)

def generate_random_title(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

app_title = generate_random_title()

CONFIG_FILE = "bot_config.cfg"

default_settings = {
    "fps": 30,
    "colors": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"],
    "blacklisted_colors": ["#000000", "#FFFFFF"],
    "bot_active": True,
    "trigger_hotkey": "k",
    "color_tolerance": 30
}

def load_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return default_settings

def save_settings(settings):
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f)

settings = load_settings()

user32, kernel32, shcore = (
    WinDLL("user32", use_last_error=True),
    WinDLL("kernel32", use_last_error=True),
    WinDLL("shcore", use_last_error=True),
)

shcore.SetProcessDpiAwareness(2)

WIDTH, HEIGHT = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]

ZONE = 5
GRAB_ZONE = (
    int(WIDTH / 2 - ZONE),
    int(HEIGHT / 2 - ZONE),
    int(WIDTH / 2 + ZONE),
    int(HEIGHT / 2 + ZONE),
)

print(f"Grab Zone: {GRAB_ZONE}")

class TriggerBot:
    def __init__(self):
        self.triggerbot = False
        self.exit_program = False
        self.is_shooting = False
        self.last_shot_time = 0
        self.shoot_cooldown = 0.150  # 200ms cooldown between shots
        self.reload_settings()

    def reload_settings(self):
        """Reload settings dynamically from the global settings variable."""
        self.trigger_hotkey = settings["trigger_hotkey"]
        self.color_tolerance = settings["color_tolerance"]
        self.colors = settings["colors"]
        self.blacklisted_colors = settings["blacklisted_colors"]
        self.fps = settings["fps"]
        self.bot_active = settings["bot_active"]
        
        self.triggerbot = self.bot_active

    def search_color(self, sct):
        try:
            img = np.array(sct.grab(GRAB_ZONE))
            img_rgba = img[:, :, [2, 1, 0, 3]]
            found_matching_color = False

            for color in self.colors:
                r, g, b = [int(color[i:i + 2], 16) for i in (1, 3, 5)]

                if self.is_color_blacklisted(r, g, b):
                    continue

                color_mask = (
                    (img_rgba[:, :, 0] > r - self.color_tolerance) & (img_rgba[:, :, 0] < r + self.color_tolerance) &
                    (img_rgba[:, :, 1] > g - self.color_tolerance) & (img_rgba[:, :, 1] < g + self.color_tolerance) &
                    (img_rgba[:, :, 2] > b - self.color_tolerance) & (img_rgba[:, :, 2] < b + self.color_tolerance)
                )

                if np.any(color_mask):
                    found_matching_color = True
                    break

            current_time = time.time()

            # Handle shooting logic with cooldown and proper key release
            if self.triggerbot and found_matching_color and keyboard.is_pressed(self.trigger_hotkey):
                if (current_time - self.last_shot_time) >= self.shoot_cooldown:
                    keyboard.press("p")  # Press 'h' to shoot
                    time.sleep(0.01)  # Short delay to simulate press
                    keyboard.release("p")  # Release 'h'
                    self.last_shot_time = current_time
                    self.is_shooting = True

            # Stop shooting if no color is found or trigger key is not pressed
            if not found_matching_color or not keyboard.is_pressed(self.trigger_hotkey):
                if self.is_shooting:
                    keyboard.release("p")  # Ensure 'h' is released if we stop shooting
                    self.is_shooting = False

        except Exception as e:
            print(f"Error in search_color: {e}")
            sys.exit()

    def is_color_blacklisted(self, r, g, b):
        """Check if the color is in the blacklist with tolerance."""
        for color in self.blacklisted_colors:
            br, bg, bb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            if (
                (r > br - self.color_tolerance) & (r < br + self.color_tolerance) &
                (g > bg - self.color_tolerance) & (g < bg + self.color_tolerance) &
                (b > bb - self.color_tolerance) & (b < bb + self.color_tolerance)
            ):
                return True
        return False

    def capture_center(self):
        try:
            sct = mss_module()
            while True:
                if self.bot_active:
                    self.search_color(sct)
                    time.sleep(1 / self.fps)  # Control FPS
                else:
                    # Ensure shooting stops when the bot is inactive
                    if self.is_shooting:
                        keyboard.release("p")  # Ensure we release the key
                        self.is_shooting = False
                    time.sleep(0.5)  # Reduce CPU usage when inactive
        except Exception as e:
            print(f"Error in capture_center: {e}")
            sys.exit()

    def run(self):
        try:
            capture_thread = threading.Thread(target=self.capture_center)
            capture_thread.daemon = True
            capture_thread.start()
        except Exception as e:
            print(f"Error in run: {e}")
            sys.exit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            settings["fps"] = int(request.form.get("fps"))
            settings["colors"] = request.form.getlist("colors")
            settings["blacklisted_colors"] = request.form.getlist("blacklisted_colors")
            settings["bot_active"] = request.form.get("bot_active") == "on"
            settings["color_tolerance"] = int(request.form.get("color_tolerance"))
            settings["trigger_hotkey"] = request.form.get("trigger_hotkey")

            if "save" in request.form:
                save_settings(settings)

            trigger_bot.reload_settings()

        except Exception as e:
            print(f"Error in settings update: {e}")

    return render_template("index.html", settings=settings, title=app_title)

def run_flask():
    try:
        app.run(debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error in Flask: {e}")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    trigger_bot = TriggerBot()
    trigger_bot.run()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit()
