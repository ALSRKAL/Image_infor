import os
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from image_metadata_viewer.imagInfo import ImageMetadataViewer
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Application entry point"""
    try:
        app = QApplication(sys.argv)
        window = ImageMetadataViewer()
        window.setWindowTitle("Image Metadata Viewer")
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()
