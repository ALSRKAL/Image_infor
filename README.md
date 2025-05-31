# Image Metadata Viewer

A cross-platform tool for viewing and managing image metadata with support for Windows, Linux, and macOS.

## 🌟 Features

- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Comprehensive Metadata**: View EXIF, IPTC, and XMP metadata
- **Multiple Formats**: Supports JPEG, PNG, TIFF, BMP, and more
- **User-Friendly**: Modern GUI with dark/light theme support
- **Export Options**: Save metadata as JSON, CSV, or text
- **Batch Processing**: Process multiple images at once
- **GPS Integration**: View image locations on maps
- **Privacy Focused**: Option to remove sensitive metadata

## 🖼️ Example Output

![Screenshot](https://user-images.githubusercontent.com/95968239/200285491-36b622f0-34d0-4261-8648-abdab3309467.jpg)

## 🖼️ Supported Image Formats

- JPEG
- PNG
- TIFF
- BMP
- GIF
- And more...

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Recommended: Using pip
```bash
pip install image-metadata-viewer
```

### From Source
1. Clone the repository:
```bash
git clone https://github.com/ALSRKAL/Image_info.git
cd Image_info
```

2. Create and activate a virtual environment:
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

## 🖥️ Usage

### Command Line
```bash
# Launch the GUI application
image-metadata-viewer

# Or use the GUI launcher (Windows/macOS)
image-metadata-viewer-gui
```

### Basic Workflow
1. Launch the application
2. Open an image using File → Open or drag and drop
3. View and explore the image metadata
4. Use the tools menu for advanced operations
5. Export metadata as needed

### Example Metadata Output

```
Filename        : image.jpg
Image Size      : (4000, 3000)
Image Height    : 3000
Image Width     : 4000
Image Format    : JPEG
Image Mode      : RGB
Make           : samsung
Model          : SM-N986B
Software       : N986BXXU4FVGA
Resolution     : 72.0 dpi
```

## 🏗️ Project Structure

```
Image_info/
├── src/
│   └── image_metadata_viewer/  # Main package
│       ├── __init__.py         # Package initialization
│       ├── __main__.py         # CLI entry point
│       ├── imagInfo.py         # Main application code
│       ├── config.py          # Configuration management
│       └── utils.py           # Utility functions
├── tests/                     # Test suite
├── docs/                      # Documentation
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── LICENSE                   # License file
├── pyproject.toml           # Build configuration
├── README.md                # This file
└── setup.py                 # Package configuration
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Run tests (`pytest`)
5. Run linters (`black . && isort . && flake8 . && mypy .`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🛠️ Development Setup

1. Install pre-commit hooks:
```bash
pre-commit install
```

2. Run tests:
```bash
pytest
```

3. Run linters:
```bash
black .
isort .
flake8 .
mypy .
```

4. Build documentation:
```bash
sphinx-build -b html docs/ docs/_build
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Thanks to PIL/Pillow for image processing
- Thanks to tkinter for GUI framework
- Thanks to all contributors
- Special thanks to alsrkal for development and maintenance
