import os
import hashlib
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_LANG = 'en'
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".image_info_cache")
RECENT_FILES_MAX = 10
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

class LanguageHandler:
    def __init__(self):
        self.current_lang = DEFAULT_LANG
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        try:
            with open(f'locales/{self.current_lang}.json', 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            self.translations = {}

    def get(self, key, default=None):
        return self.translations.get(key, default or key)

class CacheManager:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)

    def get_cache_path(self, image_path):
        return os.path.join(CACHE_DIR, hashlib.md5(image_path.encode()).hexdigest())

    def get(self, image_path):
        cache_path = self.get_cache_path(image_path)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        return None

    def set(self, image_path, data):
        cache_path = self.get_cache_path(image_path)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

def validate_image_file(file_path):
    """Validate if the file is a valid image file"""
    if not os.path.exists(file_path):
        return False, "File does not exist"
    if not os.path.isfile(file_path):
        return False, "Not a file"
    if not any(file_path.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS):
        return False, "Not a supported image format"
    return True, ""

def get_default_save_paths():
    """Get common save locations for images"""
    paths = [
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Pictures"),
        os.path.expanduser("~/Documents"),
    ]
    return [p for p in paths if os.path.exists(p)]
