import os
import json
import logging
from pathlib import Path
import platform
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIG_DIR = {
    'Windows': Path(os.getenv('APPDATA', Path.home() / '.config')) / 'image_metadata_viewer',
    'Linux': Path.home() / '.config' / 'image_metadata_viewer'
}

DEFAULT_CONFIG = {
    'version': '2.0.0',
    'language': 'en',
    'theme': 'light',
    'recent_files': [],
    'window_size': {'width': 1000, 'height': 800},
    'default_save_path': str(Path.home() / 'Downloads'),
    'map_service': 'google',
    'show_advanced_metadata': False,
    'batch_processing_size': 10,
    'last_export_format': 'json',
    'dark_mode': False,
    'font_size': 12,
    'font_family': 'Arial',
    'cache_enabled': True,
    'cache_size': 100,
    'cache_expiry_days': 7,
    'update_check_on_start': True,
    'update_channel': 'stable',
    'analytics_enabled': False,
    'analytics_id': '',
    'debug_mode': False,
    'notifications_enabled': True,
    'notification_duration': 5000,
    'notification_position': 'top-right'
}

class Config:
    def __init__(self):
        """Initialize configuration manager"""
        self.config = DEFAULT_CONFIG.copy()
        self.config_dir = DEFAULT_CONFIG_DIR.get(platform.system(), DEFAULT_CONFIG_DIR['Linux'])
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / 'config.json'
        self.load()

    def load(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Update only existing keys
                    for key in loaded_config:
                        if key in self.config:
                            self.config[key] = loaded_config[key]
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.save()

    def save(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value with fallback to default"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if key in self.config:
            self.config[key] = value
            self.save()

    def add_recent_file(self, file_path: str) -> None:
        """Add file to recent files list"""
        if not isinstance(file_path, str):
            file_path = str(file_path)
        
        recent_files = self.config['recent_files']
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        recent_files.insert(0, file_path)
        if len(recent_files) > 10:
            recent_files.pop()
        
        self.config['recent_files'] = recent_files
        self.save()

    def get_recent_files(self) -> list:
        """Get list of recent files"""
        return self.config['recent_files']

    def clear_recent_files(self) -> None:
        """Clear recent files list"""
        self.config['recent_files'] = []
        self.save()

    def get_window_size(self) -> Dict[str, int]:
        """Get window size configuration"""
        return self.config.get('window_size', {'width': 1000, 'height': 800})

    def set_window_size(self, width: int, height: int) -> None:
        """Set window size configuration"""
        self.config['window_size'] = {'width': width, 'height': height}
        self.save()

    def get_theme(self) -> str:
        """Get current theme"""
        return self.config.get('theme', 'light')

    def set_theme(self, theme: str) -> None:
        """Set theme configuration"""
        if theme in ['light', 'dark']:
            self.config['theme'] = theme
            self.config['dark_mode'] = theme == 'dark'
            self.save()

    def get_language(self) -> str:
        """Get current language"""
        return self.config.get('language', 'en')

    def set_language(self, lang: str) -> None:
        """Set language configuration"""
        self.config['language'] = lang
        self.save()

    def get_map_service(self) -> str:
        """Get current map service"""
        return self.config.get('map_service', 'google')

    def set_map_service(self, service: str) -> None:
        """Set map service configuration"""
        self.config['map_service'] = service
        self.save()

    def get_font_settings(self) -> Dict[str, Any]:
        """Get font settings"""
        return {
            'size': self.config.get('font_size', 12),
            'family': self.config.get('font_family', 'Arial')
        }

    def set_font_settings(self, size: int, family: str) -> None:
        """Set font settings"""
        self.config['font_size'] = size
        self.config['font_family'] = family
        self.save()

    def get_cache_settings(self) -> Dict[str, Any]:
        """Get cache settings"""
        return {
            'enabled': self.config.get('cache_enabled', True),
            'size': self.config.get('cache_size', 100),
            'expiry_days': self.config.get('cache_expiry_days', 7)
        }

    def set_cache_settings(self, enabled: bool, size: int, expiry_days: int) -> None:
        """Set cache settings"""
        self.config['cache_enabled'] = enabled
        self.config['cache_size'] = size
        self.config['cache_expiry_days'] = expiry_days
        self.save()

    def get_update_settings(self) -> Dict[str, Any]:
        """Get update settings"""
        return {
            'check_on_start': self.config.get('update_check_on_start', True),
            'channel': self.config.get('update_channel', 'stable')
        }

    def set_update_settings(self, check_on_start: bool, channel: str) -> None:
        """Set update settings"""
        self.config['update_check_on_start'] = check_on_start
        self.config['update_channel'] = channel
        self.save()

    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        return {
            'enabled': self.config.get('notifications_enabled', True),
            'duration': self.config.get('notification_duration', 5000),
            'position': self.config.get('notification_position', 'top-right')
        }

    def set_notification_settings(self, enabled: bool, duration: int, position: str) -> None:
        """Set notification settings"""
        self.config['notifications_enabled'] = enabled
        self.config['notification_duration'] = duration
        self.config['notification_position'] = position
        self.save()

    def get_version(self):
        return self.config.get("version", "1.0.0")

    def update_version(self, new_version):
        self.config["version"] = new_version
        self.save()
