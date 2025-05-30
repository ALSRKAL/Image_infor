import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_path = os.path.join(os.path.expanduser("~"), ".image_info_config.json")
        self.default_config = {
            "language": "en",
            "theme": "light",
            "recent_files": [],
            "window_size": {"width": 1200, "height": 800},
            "last_save_location": os.path.expanduser("~/Downloads"),
            "auto_check_updates": True,
            "dark_mode": False
        }
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config
                self.save()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def add_recent_file(self, file_path):
        if file_path in self.config["recent_files"]:
            self.config["recent_files"].remove(file_path)
        self.config["recent_files"].insert(0, file_path)
        self.config["recent_files"] = self.config["recent_files"][:10]
        self.save()
