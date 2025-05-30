# Image Metadata Viewer

A powerful tool for viewing and managing image metadata with support for multiple operating systems (Windows and Linux).

## Features

- View comprehensive image metadata
- Extract and display GPS coordinates
- Support for multiple map services
- Batch processing capabilities
- Image comparison tools
- Metadata removal utility
- Modern tabbed interface
- Dark/Light mode support
- Export to JSON and text formats
- Drag & drop support
- Recent files history
- Cross-platform compatibility

## Example Output

![Screenshot](https://user-images.githubusercontent.com/95968239/200285491-36b622f0-34d0-4261-8648-abdab3309467.jpg)

## Supported Image Formats

- JPEG
- PNG
- TIFF
- BMP
- GIF

## Installation

### Prerequisites

Make sure you have Python 3.8+ installed on your system.

### Using pip

```bash
pip install image-metadata-viewer
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/ALSRKAL/Image_info.git
cd Image_info
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

1. Launch the application
2. Open an image file using File -> Open Image or drag and drop
3. View metadata in the main window
4. Use the various tools from the Tools menu
5. Export metadata using File -> Export

## Example Metadata Output

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

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

- Thanks to PIL/Pillow for image processing
- Thanks to tkinter for GUI framework
- Thanks to all contributors
