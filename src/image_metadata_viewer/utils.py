import os
import hashlib
import json
import logging
from pathlib import Path
import platform

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_LANG = 'en'
CACHE_DIR = Path.home() / '.cache' / 'image_metadata_viewer'
RECENT_FILES_MAX = 10
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
DEFAULT_SAVE_PATHS = {
    'Windows': ['Pictures', 'Downloads', 'Desktop', 'Documents'],
    'Linux': ['Pictures', 'Downloads', 'Desktop', 'Documents']
}

class LanguageHandler:
    def __init__(self, lang_dir='locales'):
        self.current_lang = DEFAULT_LANG
        self.translations = {}
        self.lang_dir = Path(lang_dir)
        self.load_translations()

    def load_translations(self):
        try:
            lang_file = self.lang_dir / f'{self.current_lang}.json'
            if lang_file.exists():
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
            self.translations = {}

    def get(self, key, default=None):
        return self.translations.get(key, default or key)

    def set_language(self, lang):
        if lang != self.current_lang:
            self.current_lang = lang
            self.load_translations()

class CacheManager:
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = CACHE_DIR
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, image_path):
        return self.cache_dir / hashlib.md5(str(image_path).encode()).hexdigest()

    def get(self, image_path):
        cache_path = self.get_cache_path(image_path)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        return None

    def set(self, image_path, data):
        cache_path = self.get_cache_path(image_path)
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

def validate_image_file(file_path):
    """Validate if the file is a valid image file"""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return False, "File does not exist"
        if not file_path.is_file():
            return False, "Not a file"
        if not any(file_path.suffix.lower() in ext for ext in SUPPORTED_IMAGE_EXTENSIONS):
            return False, "Not a supported image format"
        return True, ""
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return False, str(e)

def get_default_save_paths():
    """Get common save locations for images"""
    system = platform.system()
    paths = DEFAULT_SAVE_PATHS.get(system, DEFAULT_SAVE_PATHS['Linux'])
    
    return [str(Path.home() / path) for path in paths if (Path.home() / path).exists()]

def get_supported_image_extensions():
    """Get list of supported image extensions"""
    return SUPPORTED_IMAGE_EXTENSIONS

def format_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(size_units) - 1:
        size_bytes /= 1024
        unit_index += 1
    
    return f"{size_bytes:.2f}{size_units[unit_index]}"
