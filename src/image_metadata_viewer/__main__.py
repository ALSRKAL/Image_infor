 #!/usr/bin/env python3
"""
Main entry point for the Image Metadata Viewer application.
"""

import os
import sys
import logging
from PyQt5.QtWidgets import QApplication

from .imagInfo import ImageMetadataViewer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
