import os
import sys
import platform
import json
import threading
import requests
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTextEdit, QFileDialog,
    QMessageBox, QMenu, QAction, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QStyle, QTableWidget, QTableWidgetItem,
    QMenuBar, QToolBar, QStatusBar, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PIL import Image, ImageEnhance, ImageFilter
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from image_metadata_viewer.utils import (
    validate_image_file, 
    get_default_save_paths,
    LanguageHandler,
    CacheManager
)
from image_metadata_viewer.config import Config

class ImageMetadataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle(self.config.get("app_title", "Image Metadata Viewer"))
        self.setGeometry(100, 100, 1000, 800)
        
        # Initialize brightness and contrast variables
        self.brightness_var = 1.0
        self.contrast_var = 1.0
        self.original_image = None
        self.preview_photo = None
        
        # Initialize status bar first
        self.status_var = QLabel("Initializing...")
        status_bar = self.statusBar()
        status_bar.addWidget(self.status_var)
        self.status_var.setObjectName("statusLabel")  # For styling if needed
        
        # Initialize variables
        self.current_image_path = None
        self.image_data = None
        self.recent_files = []
        self.dark_mode = False
        self.info_labels = {}  # Initialize info_labels dictionary
        
        # Initialize map services
        self.maps_services = [
            ('Google Maps', 'https://www.google.com/maps?q={},{}'),
            ('OpenStreetMap', 'https://www.openstreetmap.org/?mlat={}&mlon={}'),
            ('Bing Maps', 'https://www.bing.com/maps?cp={}~{}')
        ]
        self.current_lat = None
        self.current_lon = None
        self.current_url = None
        
        # Initialize map service buttons
        self.open_maps_button = None
        self.copy_url_button = None
        
        # Load system-specific settings
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.system_settings = settings.get('system', {})
                self.window_settings = settings.get('window', {
                    'width': 800, 'height': 600, 
                    'min_width': 400, 'min_height': 300
                })
                self.appearance = settings.get('appearance', {'theme': 'light'})
                self.current_settings = self.system_settings.get(
                    platform.system().lower(), 
                    self.system_settings.get('linux', {})
                )
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.system_settings = {}
            self.window_settings = {'width': 800, 'height': 600, 'min_width': 400, 'min_height': 300}
            self.appearance = {'theme': 'light'}
            self.current_settings = {}
        
        # Set window size
        self.resize(self.window_settings['width'], self.window_settings['height'])
        self.setMinimumSize(self.window_settings['min_width'], self.window_settings['min_height'])
        
        # Update file dialog options
        self.file_dialog_options = self.current_settings.get('file_dialog', {
            'title': 'Open Image File',
            'filetypes': [('Image files', '*.jpg *.jpeg *.png *.gif *.bmp *.tiff')]
        })
        
        # Set window icon
        try:
            icon_path = os.path.expanduser(self.current_settings.get('icon', ''))
            if icon_path and os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass
            
        # Load recent files
        self.load_recent_files()
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        
        # Setup UI components
        self.setWindowTitle(self.config.get("app_title", "Image Metadata Viewer"))
        self.setGeometry(100, 100, 800, 600)
        self.create_menu()
        self.create_widgets()
        
        # Update status
        self.status_var.setText("Ready - Drag and drop images or click Open to get started")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        
        # Load recent files
        self.load_recent_files()
        
        # Set system-specific settings
        self.system = platform.system()
        self.current_settings = self.system_settings.get(self.system.lower(), self.system_settings['linux'])
        
        # Set window size
        self.resize(self.window_settings['width'], self.window_settings['height'])
        self.setMinimumSize(self.window_settings['min_width'], self.window_settings['min_height'])
        
        # Set window icon
        try:
            icon_path = os.path.expanduser(self.current_settings.get('icon', ''))
            if icon_path and os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass
            
        # Update file dialog options
        self.file_dialog_options = self.current_settings.get('file_dialog', {
            'title': 'Open Image File',
            'filetypes': [('Image files', '*.jpg *.jpeg *.png *.gif *.bmp *.tiff')]
        })
        
        # Initialize components
        self.cache = CacheManager()
        self.lang = LanguageHandler()
        self.progress_var = 0.0
        
        # Variables
        self.current_url = None
        self.current_image_path = None
        self.recent_files = []
        self.dark_mode = False
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)

        # Load recent files
        self.load_recent_files()

        # Setup UI
        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.setup_drag_drop()

    def setup_styles(self):
        """Setup modern styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)

    def create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&Open Image...", self.open_image, "Ctrl+O")
        file_menu.addSeparator()

        # Recent files submenu
        self.recent_menu = file_menu.addMenu("&Recent Files")
        self.update_recent_menu()

        file_menu.addSeparator()
        file_menu.addAction("&Save Metadata...", self.save_metadata_to_file, "Ctrl+S")
        file_menu.addAction("&Export as JSON...", self.export_json)
        file_menu.addSeparator()
        file_menu.addAction("&Exit", self.close)

        # View menu
        view_menu = menubar.addMenu("&View")
        dark_mode_action = QAction("&Dark Mode", self)
        dark_mode_action.setCheckable(True)
        dark_mode_action.setChecked(False)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        view_menu.addAction("&Refresh", self.refresh_current_image, "F5")

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction("&Batch Process...", self.batch_process)
        tools_menu.addAction("&Compare Images...", self.compare_images)
        tools_menu.addAction("&Remove Metadata...", self.remove_metadata)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self.show_about)

    def create_widgets(self):
        """Create main widgets"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar.setLayout(toolbar_layout)
        
        # Add toolbar buttons
        open_btn = QPushButton("Open Image")
        open_btn.clicked.connect(self.open_image)
        toolbar_layout.addWidget(open_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_current_image)
        toolbar_layout.addWidget(refresh_btn)
        
        main_layout.addWidget(toolbar)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create GPS tab
        gps_tab = QWidget()
        gps_layout = QVBoxLayout(gps_tab)
        
        # GPS info display
        self.gps_text = QTextEdit()
        self.gps_text.setReadOnly(True)
        self.gps_text.setAcceptRichText(True)  # Enable rich text formatting
        gps_layout.addWidget(self.gps_text)
        
        # GPS control buttons
        gps_button_frame = QFrame()
        gps_button_layout = QHBoxLayout(gps_button_frame)
        gps_button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Add map service buttons
        for service_name, _ in self.maps_services:
            btn = QPushButton(f"📍 {service_name}")
            btn.clicked.connect(lambda checked, name=service_name: self.open_service_url(name))
            btn.setEnabled(False)
            gps_button_layout.addWidget(btn)
            setattr(self, f"{service_name.lower().replace(' ', '_')}_button", btn)
        
        # Add open maps and copy URL buttons
        self.open_maps_button = QPushButton("Open in Default Maps")
        self.open_maps_button.clicked.connect(self.open_in_default_maps)
        self.open_maps_button.setEnabled(False)
        gps_button_layout.addWidget(self.open_maps_button)
        
        self.copy_url_button = QPushButton("Copy URL")
        self.copy_url_button.clicked.connect(self.copy_maps_url)
        self.copy_url_button.setEnabled(False)
        gps_button_layout.addWidget(self.copy_url_button)
        
        gps_layout.addWidget(gps_button_frame)
        self.tabs.addTab(gps_tab, "🌍 GPS Location")
        
        # Create Metadata tab
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        
        # Create a scroll area for the metadata
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Create a widget to contain the metadata text
        metadata_content = QWidget()
        layout = QVBoxLayout(metadata_content)
        
        # Create the text edit for metadata
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setLineWrapMode(QTextEdit.NoWrap)
        font = self.metadata_text.font()
        font.setFamily('Monospace')
        font.setPointSize(10)
        self.metadata_text.setFont(font)
        
        layout.addWidget(self.metadata_text)
        scroll.setWidget(metadata_content)
        metadata_layout.addWidget(scroll)
        
        self.tabs.addTab(metadata_tab, "📋 Metadata")
        
        # Create preview panel
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        self.tabs.addTab(preview_tab, "👁️ Preview")
        
        # Set the layout
        central_widget.setLayout(main_layout)

    def create_toolbar(self, parent):
        """Create toolbar with essential buttons"""
        toolbar = QFrame(parent)
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Add only the most commonly used actions to the toolbar
        actions = [
            ("📂 Open", self.open_image, "Open an image file"),
            ("🔄 Refresh", self.refresh_current_image, "Refresh the current view"),
            ("💾 Save", self.save_metadata_to_file, "Save metadata to file"),
            ("📊 Export", self.export_json, "Export as JSON")
        ]
        
        for text, callback, tooltip in actions:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setToolTip(tooltip)
            toolbar_layout.addWidget(btn)
        
        # Add a spacer to push the help button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # Add a help button
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(self.show_about)
        help_btn.setToolTip("Show help and about information")
        toolbar_layout.addWidget(help_btn)
        
        parent.layout().addWidget(toolbar)
        
        # Set toolbar styles
        toolbar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        toolbar.addWidget(export_button)

    def create_metadata_tab(self, parent):
        """Create metadata display tab"""
        # Search frame
        search_frame = QFrame(parent)
        search_frame.setContentsMargins(0, 0, 0, 10)
        search_frame.setLayout(QHBoxLayout())

        search_label = QLabel("🔍 Search:")
        search_frame.layout().addWidget(search_label)
        self.search_var = QComboBox()
        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Search metadata...")
        search_entry.setMinimumWidth(200)
        search_frame.layout().addWidget(search_entry)

        # Metadata display with tree view
        tree_frame = QFrame(parent)
        tree_frame.setContentsMargins(0, 0, 0, 0)
        tree_frame.setLayout(QVBoxLayout())

        # Treeview for structured metadata display
        self.metadata_tree = QTreeWidget()
        self.metadata_tree.setHeaderLabels(['Property', 'Value'])
        self.metadata_tree.setColumnWidth(0, 200)
        # Configure tree view headers
        self.metadata_tree.setHeaderLabels(['Property', 'Value'])
        self.metadata_tree.setColumnWidth(0, 200)
        
        # Configure tree view columns
        self.metadata_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.metadata_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Configure tree view scrollbars
        self.metadata_tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.metadata_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Pack treeview and scrollbars
        self.metadata_tree.setHorizontalScrollBar(h_scrollbar)
        self.metadata_tree.setVerticalScrollBar(v_scrollbar)
        tree_frame.layout().addWidget(self.metadata_tree)

        # Context menu for treeview
        self.create_context_menu()

    def create_gps_tab(self, parent):
        """GPS tab creation is now handled in create_widgets"""
        pass

    def create_info_tab(self, parent):
        """Create image information tab"""
        info_label = QLabel("Image Properties")
        info_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        info_label.setContentsMargins(0, 0, 0, 10)
        parent.layout().addWidget(info_label)

        # Image info frame
        info_frame = QFrame(parent)
        info_frame.setContentsMargins(0, 0, 0, 0)
        info_frame.setLayout(QGridLayout())
        info_frame.layout().setColumnStretch(1, 1)

        # Create labels for image info
        self.info_labels = {}
        info_items = [
            ('filename', 'Filename:'),
            ('filepath', 'File Path:'),
            ('filesize', 'File Size:'),
            ('dimensions', 'Dimensions:'),
            ('format', 'Format:'),
            ('mode', 'Color Mode:'),
            ('created', 'Created:'),
            ('modified', 'Modified:'),
            ('hash', 'MD5 Hash:')
        ]

        for i, (key, label) in enumerate(info_items):
            label = QLabel(label)
            label.setStyleSheet("font-weight: bold;")
            info_frame.layout().addWidget(label, i, 0, Qt.AlignLeft)
            self.info_labels[key] = QLabel('-')
            self.info_labels[key].setWordWrap(True)
            info_frame.layout().addWidget(self.info_labels[key], i, 1, Qt.AlignLeft)

    def create_preview_panel(self, parent):
        """Create image preview panel"""
        preview_label = QLabel("Image Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        preview_label.setContentsMargins(0, 0, 0, 10)
        parent.layout().addWidget(preview_label)

        # Preview canvas with scrollbar
        canvas_frame = QFrame(parent)
        canvas_frame.setContentsMargins(0, 0, 0, 0)
        canvas_frame.setLayout(QVBoxLayout())

        self.preview_canvas = QLabel()
        self.preview_canvas.setStyleSheet("background-color: white;")
        preview_scrollbar_v = QScrollBar(Qt.Vertical)
        preview_scrollbar_h = QScrollBar(Qt.Horizontal)

        # Connect scrollbars to canvas
        preview_scrollbar_v.valueChanged.connect(self.preview_canvas.setVerticalScrollBarValue)
        preview_scrollbar_h.valueChanged.connect(self.preview_canvas.setHorizontalScrollBarValue)

        self.preview_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_frame.layout().addWidget(self.preview_canvas)

        # Image adjustment controls
        adjust_frame = QGroupBox("Image Adjustments")
        adjust_frame.setContentsMargins(0, 10, 0, 0)
        adjust_frame.setLayout(QGridLayout())
        adjust_frame.layout().setColumnStretch(1, 1)
        adjust_frame = QGroupBox("Image Adjustments")
        adjust_frame.setContentsMargins(0, 10, 0, 0)
        adjust_frame.setLayout(QGridLayout())
        adjust_frame.layout().setColumnStretch(1, 1)

        # Brightness
        brightness_label = QLabel("Brightness:")
        adjust_frame.layout().addWidget(brightness_label, 0, 0, Qt.AlignLeft)
        self.brightness_var = QDoubleSpinBox()
        self.brightness_var.setRange(0.1, 2.0)
        self.brightness_var.setValue(1.0)
        self.brightness_var.valueChanged.connect(self.update_preview)
        adjust_frame.layout().addWidget(self.brightness_var, 0, 1)

        # Contrast
        contrast_label = QLabel("Contrast:")
        adjust_frame.layout().addWidget(contrast_label, 1, 0, Qt.AlignLeft)
        self.contrast_var = QDoubleSpinBox()
        self.contrast_var.setRange(0.1, 2.0)
        self.contrast_var.setValue(1.0)
        self.contrast_var.valueChanged.connect(self.update_preview)
        adjust_frame.layout().addWidget(self.contrast_var, 1, 1)

        adjust_frame.layout().setColumnStretch(1, 1)

        # Reset button

    def init_status_bar(self):
        """Initialize the status bar (kept for backward compatibility)"""
        pass

    def create_context_menu(self):
        """Create context menu for metadata tree"""
        self.context_menu = QMenu(self)
        self.context_menu.addAction("Copy Value", self.copy_selected_value)
        self.context_menu.addAction("Copy Property", self.copy_selected_property)
        self.metadata_tree.customContextMenuRequested.connect(self.show_context_menu)

    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.open_image(url.toLocalFile())
        event.acceptProposedAction()

    def handle_drop(self, event):
        """Handle dropped files"""
        files = self.root.splitlist(event.data)
        if files:
            self.load_image(files[0])

    def read_metadata(self, image_path):
        """Read and return image metadata as a dictionary"""
        try:
            with Image.open(image_path) as img:
                metadata = img._getexif()
                if metadata:
                    result = {}
                    for tag_id, value in metadata.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        result[tag_name] = value
                    return result
                return {}
        except Exception as e:
            print(f"Error reading metadata: {e}")
            return {}

    def get_image_metadata(self, image_path):
        """Extract metadata from image (legacy method)"""
        return self.read_metadata(image_path)
        try:
            image = Image.open(image_path)
            metadata = image._getexif()

            if metadata:
                structured_metadata = {}
                for tag_id, value in metadata.items():
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    structured_metadata[tag_name] = str(value)
                return structured_metadata
            else:
                return {}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading metadata: {e}")
            return {}

    def get_image_location(self, image_path):
        """Extract GPS location from image"""
        try:
            image = Image.open(image_path)
            metadata = image._getexif()

            if metadata:
                gps_info = metadata.get(34853, {})
                if gps_info:
                    lat = gps_info.get(2, None)
                    lat_ref = gps_info.get(1, None)
                    lon = gps_info.get(4, None)
                    lon_ref = gps_info.get(3, None)

                    if all([lat, lat_ref, lon, lon_ref]):
                        lat_decimal = self.get_decimal_from_dms(lat, lat_ref)
                        lon_decimal = self.get_decimal_from_dms(lon, lon_ref)
                        return lat_decimal, lon_decimal, gps_info
            return None, None, {}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading GPS data: {e}")
            return None, None, {}

    def get_decimal_from_dms(self, dms, ref):
        """Convert DMS to decimal degrees"""
        degrees = dms[0]
        minutes = dms[1] / 60.0
        seconds = dms[2] / 3600.0
        decimal = degrees + minutes + seconds

        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    def open_image(self):
        """Open modern file dialog to select image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select an Image",
            "",
            "Images (*.jpg *.jpeg *.png *.tiff *.bmp *.gif)"
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        """Load and analyze image"""
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", "File not found!")
            return

        self.status_var.setText("Loading image...")
        QApplication.processEvents()  # Update UI

        try:
            self.current_image_path = file_path

            # Add to recent files
            if file_path not in self.recent_files:
                self.recent_files.insert(0, file_path)
                self.recent_files = self.recent_files[:10]
                self.save_recent_files()
                if hasattr(self, 'update_recent_menu'):
                    self.update_recent_menu()

            # Load and display metadata
            metadata = self.read_metadata(file_path)
            self.display_metadata(metadata)

            # Load GPS info
            lat, lon, gps_info = self.get_image_location(file_path)
            self.display_gps_info(lat, lon, gps_info)

            # Load image info
            self.display_image_info(file_path)

            
            # Load preview
            self.load_preview(file_path)
            
            self.status_var.setText(f"Loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
            self.status_var.setText("Error loading image")
            print(f"Error loading image: {str(e)}")

    def format_metadata_value(self, value):
        """Format metadata value for display"""
        if value is None:
            return "<i>None</i>"
        elif isinstance(value, (bytes, bytearray)):
            return "<i>binary data</i>"
        elif isinstance(value, str):
            if len(value) > 100:
                return f"{value[:100]}..."
            return value
        elif isinstance(value, (list, tuple, dict, set)):
            return ", ".join(str(v) for v in value) if value else "<i>Empty</i>"
        return str(value)

    def group_metadata(self, metadata):
        """Group metadata into categories for better organization"""
        groups = {
            'Basic Information': {},
            'Camera Settings': {},
            'Image Properties': {},
            'File Information': {},
            'GPS Data': {},
            'Other': {}
        }
        
        # Common metadata groups
        camera_keys = ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 
                      'FocalLength', 'ExposureProgram', 'MeteringMode', 'Flash', 'WhiteBalance']
        image_keys = ['Width', 'Height', 'Orientation', 'Resolution', 'ColorSpace', 'XResolution', 
                     'YResolution', 'ResolutionUnit']
        file_keys = ['FileName', 'FileSize', 'FileType', 'MIMEType', 'ModifyDate', 'CreateDate']
        gps_keys = ['GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSSpeed', 'GPSImgDirection']
        
        for key, value in metadata.items():
            key_str = str(key)
            if any(k in key_str for k in camera_keys):
                groups['Camera Settings'][key_str] = value
            elif any(k in key_str for k in image_keys):
                groups['Image Properties'][key_str] = value
            elif any(k in key_str for k in file_keys):
                groups['File Information'][key_str] = value
            elif any(k in key_str for k in gps_keys):
                groups['GPS Data'][key_str] = value
            else:
                groups['Other'][key_str] = value
                
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def display_metadata(self, metadata):
        """Display metadata in a well-formatted way in the text area with enhanced UI/UX"""
        try:
            if not hasattr(self, 'metadata_text'):
                print("Metadata text widget not found")
                return
                
            if not metadata:
                self.metadata_text.setHtml("""
                    <div style='padding: 20px; text-align: center; color: #666; font-style: italic;'>
                        No metadata found in the image.
                    </div>
                """)
                return
            
            # Group metadata into categories
            grouped_metadata = self.group_metadata(metadata)
            
            # Theme colors based on dark mode
            bg_color = "#1e1e1e" if self.dark_mode else "#ffffff"
            text_color = "#e0e0e0" if self.dark_mode else "#333333"
            header_bg = "#2d2d2d" if self.dark_mode else "#f0f0f0"
            border_color = "#444" if self.dark_mode else "#dee2e6"
            row_even = "#252526" if self.dark_mode else "#f8f9fa"
            row_hover = "#383838" if self.dark_mode else "#f1f8ff"
            
            # Generate HTML content
            html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        margin: 0;
                        padding: 15px;
                        background-color: {bg_color};
                        color: {text_color};
                        font-size: 14px;
                    }}
                    .header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        flex-wrap: wrap;
                        gap: 10px;
                    }}
                    .search-box {{
                        padding: 8px 12px;
                        border: 1px solid {border_color};
                        border-radius: 4px;
                        background-color: {bg_color};
                        color: {text_color};
                        min-width: 250px;
                        font-size: 14px;
                    }}
                    h2 {{ 
                        color: {text_color};
                        border-bottom: 1px solid {border_color};
                        padding-bottom: 8px;
                        margin: 25px 0 15px 0;
                        font-size: 1.3em;
                    }}
                    .metadata-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 10px 0 25px 0;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }}
                    .metadata-table th {{
                        text-align: left;
                        background-color: {header_bg};
                        padding: 10px 12px;
                        border: 1px solid {border_color};
                        cursor: pointer;
                        position: relative;
                        user-select: none;
                        font-weight: 500;
                    }}
                    .metadata-table th:hover {{
                        background-color: {row_hover};
                    }}
                    .metadata-table th.sort-asc::after {{
                        content: ' ↑';
                        font-size: 0.9em;
                        opacity: 0.7;
                    }}
                    .metadata-table th.sort-desc::after {{
                        content: ' ↓';
                        font-size: 0.9em;
                        opacity: 0.7;
                    }}
                    .metadata-table td {{
                        padding: 10px 12px;
                        border: 1px solid {border_color};
                        vertical-align: top;
                        font-family: 'Consolas', 'Monaco', monospace;
                        word-break: break-word;
                        max-width: 500px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }}
                    .metadata-table tr:nth-child(even) {{
                        background-color: {row_even};
                    }}
                    .metadata-table tr:hover {{
                        background-color: {row_hover};
                    }}
                    .empty {{
                        color: #888;
                        font-style: italic;
                    }}
                    .copy-btn {{
                        background: none;
                        border: 1px solid {border_color};
                        border-radius: 3px;
                        color: {text_color};
                        cursor: pointer;
                        margin-left: 8px;
                        padding: 2px 6px;
                        font-size: 0.8em;
                        opacity: 0.7;
                        transition: opacity 0.2s;
                    }}
                    .copy-btn:hover {{
                        opacity: 1;
                        background: rgba(255,255,255,0.1);
                    }}
                    .tooltip {{
                        position: relative;
                        display: inline-block;
                        border-bottom: 1px dotted #666;
                        cursor: help;
                        margin-left: 5px;
                    }}
                    .tooltip .tooltiptext {{
                        visibility: hidden;
                        width: 200px;
                        background-color: #333;
                        color: #fff;
                        text-align: center;
                        border-radius: 4px;
                        padding: 5px;
                        position: absolute;
                        z-index: 1;
                        bottom: 125%;
                        left: 50%;
                        margin-left: -100px;
                        opacity: 0;
                        transition: opacity 0.3s;
                        font-size: 12px;
                    }}
                    .tooltip:hover .tooltiptext {{
                        visibility: visible;
                        opacity: 1;
                    }}
                    @media (max-width: 768px) {{
                        .metadata-table {{
                            display: block;
                            overflow-x: auto;
                            white-space: nowrap;
                        }}
                        .header {{
                            flex-direction: column;
                            align-items: flex-start;
                        }}
                        .search-box {{
                            width: 100%;
                            margin-top: 10px;
                        }}
                    }}
                </style>
                <script>
                    function copyToClipboard(text, btn) {{
                        navigator.clipboard.writeText(text).then(function() {{
                            const original = btn.innerHTML;
                            btn.innerHTML = 'Copied!';
                            btn.style.color = '#4CAF50';
                            setTimeout(function() {{
                                btn.innerHTML = original;
                                btn.style.color = '';
                            }}, 2000);
                        }}).catch(function(err) {{
                            console.error('Could not copy text: ', err);
                        }});
                    }}
                    
                    function sortTable(table, col, dir) {{
                        const tbody = table.querySelector('tbody');
                        const rows = Array.from(tbody.rows);
                        const isNum = rows.every(row => !isNaN(parseFloat(row.cells[col].textContent)));
                        
                        rows.sort((a, b) => {{
                            let valA = a.cells[col].textContent;
                            let valB = b.cells[col].textContent;
                            
                            if (isNum) {{
                                valA = parseFloat(valA) || 0;
                                valB = parseFloat(valB) || 0;
                                return dir === 'asc' ? valA - valB : valB - valA;
                            }} else {{
                                return dir === 'asc' 
                                    ? valA.localeCompare(valB)
                                    : valB.localeCompare(valA);
                            }}
                        }});
                        
                        // Remove existing rows
                        while (tbody.firstChild) {{
                            tbody.removeChild(tbody.firstChild);
                        }}
                        
                        // Add sorted rows
                        rows.forEach(row => tbody.appendChild(row));
                    }}
                    
                    function initSorting() {{
                        document.querySelectorAll('.metadata-table th').forEach((th, i) => {{
                            th.addEventListener('click', () => {{
                                const table = th.closest('table');
                                const isAsc = th.classList.contains('sort-asc');
                                const isDesc = th.classList.contains('sort-desc');
                                
                                // Reset all sort indicators
                                table.querySelectorAll('th').forEach(h => {{
                                    h.classList.remove('sort-asc', 'sort-desc');
                                }});
                                
                                // Set new sort indicator
                                if (!isAsc && !isDesc) {{
                                    th.classList.add('sort-asc');
                                    sortTable(table, i, 'asc');
                                }} else if (isAsc) {{
                                    th.classList.add('sort-desc');
                                    sortTable(table, i, 'desc');
                                }} else {{
                                    // If already sorted desc, reset to original order
                                    const tbody = table.querySelector('tbody');
                                    const rows = Array.from(tbody.rows);
                                    rows.sort((a, b) => a.dataset.originalIndex - b.dataset.originalIndex);
                                    tbody.innerHTML = '';
                                    rows.forEach(row => tbody.appendChild(row));
                                }}
                            }});
                        }});
                        
                        // Store original row order for resetting
                        document.querySelectorAll('.metadata-table tbody tr').forEach((row, i) => {{
                            row.dataset.originalIndex = i;
                        }});
                    }}
                    
                    function filterTable() {{
                        const input = document.getElementById('searchInput');
                        const filter = input.value.toLowerCase();
                        const tables = document.querySelectorAll('.metadata-table');
                        
                        tables.forEach(table => {{
                            const rows = table.querySelectorAll('tbody tr');
                            let hasVisibleRows = false;
                            
                            rows.forEach(row => {{
                                const text = row.textContent.toLowerCase();
                                const isVisible = text.includes(filter);
                                row.style.display = isVisible ? '' : 'none';
                                if (isVisible) hasVisibleRows = true;
                            }});
                            
                            // Show/hide section header based on visibility
                            const sectionHeader = table.previousElementSibling;
                            if (sectionHeader && sectionHeader.tagName === 'H2') {{
                                sectionHeader.style.display = hasVisibleRows ? '' : 'none';
                            }}
                        }});
                    }}
                    
                    document.addEventListener('DOMContentLoaded', function() {{
                        initSorting();
                        
                        // Add event listener for search input
                        const searchInput = document.getElementById('searchInput');
                        if (searchInput) {{
                            searchInput.addEventListener('input', filterTable);
                            searchInput.focus();
                        }}
                    }});
                </script>
            </head>
            <body>
                <div class="header">
                    <h2>Image Metadata</h2>
                    <div>
                        <input type="text" id="searchInput" class="search-box" 
                               placeholder="Search metadata..." 
                               title="Type to filter metadata">
                    </div>
                </div>
            """
            
            # Add metadata sections
            for group_name, group_items in sorted(grouped_metadata.items()):
                if not group_items:
                    continue
                    
                html += f"<h2>{group_name}</h2>"
                html += "<div style='overflow-x: auto;'>"
                html += "<table class='metadata-table'>"
                html += """
                    <thead>
                        <tr>
                            <th>Property <span class="tooltip">ⓘ<span class="tooltiptext">Click to sort</span></span></th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for key, value in sorted(group_items.items()):
                    formatted_value = self.format_metadata_value(value)
                    display_value = str(formatted_value).replace('\n', '<br>') if formatted_value is not None else '<span class="empty">(empty)</span>'
                    copy_value = str(formatted_value).replace('"', '&quot;')
                    
                    html += f"""
                        <tr>
                            <td style='min-width: 200px;'><b>{key}</b></td>
                            <td>
                                <div style='display: flex; align-items: center; justify-content: space-between;'>
                                    <span style='flex: 1;'>{display_value}</span>
                                    <button class="copy-btn" 
                                            onclick="copyToClipboard('{copy_value}', this)"
                                            title="Copy to clipboard">
                                        📋
                                    </button>
                                </div>
                            </td>
                        </tr>
                    """
                
                html += """
                    </tbody>
                    </table>
                    </div>
                """
            
            html += """
                <script>
                    // Initialize tooltips
                    document.addEventListener('DOMContentLoaded', function() {
                        const tooltips = document.querySelectorAll('.tooltip');
                        tooltips.forEach(tooltip => {
                            tooltip.addEventListener('click', (e) => e.preventDefault());
                        });
                    });
                </script>
                </body>
                </html>
            """
            
            # Set the HTML content
            self.metadata_text.setHtml(html)
            self.metadata_text.setVisible(True)
            
            # Switch to the Metadata tab
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "📋 Metadata":
                    self.tabs.setCurrentIndex(i)
                    break
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in display_metadata: {error_details}")
            error_msg = f"""
            <div style='padding: 20px; color: #ff6b6b; background: #fff0f0; border-radius: 5px; margin: 10px;'>
                <h3 style='margin-top: 0;'>Error displaying metadata</h3>
                <p>{str(e)}</p>
                <details style='margin-top: 10px;'>
                    <summary style='cursor: pointer; color: #cc0000;'>Show details</summary>
                    <pre style='background: #f8f8f8; padding: 10px; border-radius: 3px; overflow: auto;'>{error_details}</pre>
                </details>
            </div>
            """
            self.metadata_text.setHtml(error_msg)














    def get_decimal_from_dms(self, dms, ref):
        """Convert DMS to decimal degrees"""
        degrees = dms[0]
        minutes = dms[1] / 60.0
        seconds = dms[2] / 3600.0
        decimal = degrees + minutes + seconds

        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    def display_gps_info(self, lat, lon, gps_info):
        """Display GPS information in the GPS tab"""
        if not hasattr(self, 'gps_text'):
            return

        if lat is not None and lon is not None:
            gps_text = "<p><b>📍 GPS Coordinates Found!</b></p>"
            gps_text += f"<p>Latitude: {lat:.6f}°<br>"
            gps_text += f"Longitude: {lon:.6f}°</p>"
            gps_text += f"<p>Decimal Degrees: {lat:.6f}, {lon:.6f}</p>"
            
            if gps_info:
                gps_text += "<p><b>Additional GPS Data:</b><br>"
                for key, value in gps_info.items():
                    tag_name = GPSTAGS.get(key, f"GPS_{key}")
                    gps_text += f"{tag_name}: {value}<br>"
                gps_text += "</p>"

            # Enable map service buttons
            for service_name, _ in self.maps_services:
                btn_name = f"{service_name.lower().replace(' ', '_')}_button"
                if hasattr(self, btn_name):
                    getattr(self, btn_name).setEnabled(True)

            if hasattr(self, 'open_maps_button'):
                self.open_maps_button.setEnabled(True)
            if hasattr(self, 'copy_url_button'):
                self.copy_url_button.setEnabled(True)

            self.current_lat = lat
            self.current_lon = lon
            self.current_url = f"https://www.google.com/maps?q={lat},{lon}"

        else:
            gps_text = "<p><b>❌ No GPS data found in this image.</b></p>"
            gps_text += "<p>GPS coordinates are typically embedded in photos taken with:<br>"
            gps_text += "• Smartphones with location services enabled<br>"
            gps_text += "• Cameras with built-in GPS<br>"
            gps_text += "• Images geotagged manually</p>"

            # Disable map service buttons
            for service_name, _ in self.maps_services:
                btn_name = f"{service_name.lower().replace(' ', '_')}_button"
                if hasattr(self, btn_name):
                    getattr(self, btn_name).setEnabled(False)

            if hasattr(self, 'open_maps_button'):
                self.open_maps_button.setEnabled(False)
            if hasattr(self, 'copy_url_button'):
                self.copy_url_button.setEnabled(False)

        self.gps_text.setHtml(gps_text)

    def display_image_info(self, file_path):
        """Display image file information"""
        try:
            stat = os.stat(file_path)
            self.info_labels['filename'].setText(os.path.basename(file_path))
            self.info_labels['filepath'].setText(file_path)
            self.info_labels['filesize'].setText(f"{stat.st_size:,} bytes ({stat.st_size/1024/1024:.2f} MB)")
            self.info_labels['created'].setText(datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'))
            self.info_labels['modified'].setText(datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))

            with Image.open(file_path) as img:
                self.info_labels['dimensions'].setText(f"{img.width} × {img.height} pixels")
                self.info_labels['format'].setText(img.format or 'Unknown')
                self.info_labels['mode'].setText(img.mode)

            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            self.info_labels['hash'].setText(hash_md5.hexdigest())

        except Exception as e:
            for label in self.info_labels.values():
                label.setText('Error')

    def load_preview(self, file_path):
        """Load image preview"""
        try:
            self.original_image = Image.open(file_path)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preview: {e}")

    def update_preview(self):
        """Update preview with current adjustments"""
        if not hasattr(self, 'original_image') or self.original_image is None:
            return

        try:
            img = self.original_image.copy()

            # Apply brightness and contrast if available
            if hasattr(self, 'brightness_var'):
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(self.brightness_var)

            if hasattr(self, 'contrast_var'):
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(self.contrast_var)

            # Convert to RGB if needed (QImage doesn't support all modes)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize for preview
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)

            # Convert PIL Image to QPixmap
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.size[0], img.size[1], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Update the preview label
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setAlignment(Qt.AlignCenter)

        except Exception as e:
            print(f"Preview update error: {str(e)}")

    def filter_metadata(self, *args):
        """Filter metadata based on search term"""
        pass  # Placeholder for search functionality

    def adjust_preview(self, *args):
        """Adjust preview image"""
        self.update_preview()

    def reset_adjustments(self):
        """Reset image adjustments"""
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.update_preview()

    def open_in_google_maps(self):
        """Open location in Google Maps"""
        if self.current_url:
            webbrowser.open(self.current_url)

    def open_service_url(self, service_name):
        """Open the selected map service with current coordinates"""
        if not hasattr(self, 'current_lat') or not hasattr(self, 'current_lon') or \
           self.current_lat is None or self.current_lon is None:
            self.status_var.setText("No coordinates available")
            return
            
        for name, url_template in self.maps_services:
            if name == service_name:
                try:
                    if 'bing' in name.lower():
                        url = url_template.format(self.current_lat, self.current_lon)
                    else:
                        url = url_template.format(self.current_lat, self.current_lon)
                    webbrowser.open(url)
                    self.status_var.setText(f"Opened in {service_name}")
                    return
                except Exception as e:
                    self.status_var.setText(f"Error opening {service_name}: {str(e)}")
                    return
        
        self.status_var.setText(f"Service {service_name} not found")
    
    def open_in_default_maps(self):
        """Open coordinates in the system's default maps application"""
        if not hasattr(self, 'current_lat') or not hasattr(self, 'current_lon') or \
           self.current_lat is None or self.current_lon is None:
            self.status_var.setText("No coordinates available")
            return
            
        # Use the first available map service as default
        if self.maps_services:
            service_name, _ = self.maps_services[0]
            self.open_service_url(service_name)
    
    def copy_maps_url(self):
        """Copy the current maps URL to clipboard"""
        if hasattr(self, 'current_url') and self.current_url:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_url)
            self.status_var.setText("URL copied to clipboard!")
        else:
            self.status_var.setText("No URL available to copy")

    def copy_selected_property(self):
        """Copy selected metadata property name"""
        selected_items = self.metadata_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            property_name = item.text(0)
            pyperclip.copy(property_name)
            QMessageBox.information(self, "Copied", "Property name copied to clipboard!")

    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.exec_(self.mapToGlobal(event.pos()))
        finally:
            self.context_menu.grab_release()

    def clear_all(self):
        """Clear all data"""
        for item in self.metadata_tree.get_children():
            self.metadata_tree.delete(item)

        self.gps_textbox.delete(1.0, tk.END)

        for label in self.info_labels.values():
            label.setText('-')

        self.preview_label.clear()

        self.current_image_path = None
        self.current_url = None

        self.open_maps_button.setEnabled(False)
        self.copy_url_button.setEnabled(False)
        for service_name, _ in self.maps_services:
            btn_name = f"{service_name.lower().replace(' ', '_')}_button"
            if hasattr(self, btn_name):
                getattr(self, btn_name).setEnabled(False)

        self.reset_adjustments()

        self.status_var.set("Ready")

    def refresh_current_image(self):
        """Refresh current image"""
        if self.current_image_path and os.path.exists(self.current_image_path):
            self.load_image(self.current_image_path)
        else:
            QMessageBox.warning(self, "Warning", "No image loaded or file not found!")

    def export_json(self):
        """Export metadata to JSON file"""
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            QMessageBox.warning(self, "Warning", "No image loaded!")
            return

        file_path = QFileDialog.getSaveFileName(
            self,
            "Export as JSON",
            "",
            "JSON Files (*.json)"
        )[0]

        if file_path:
            try:
                metadata = self.get_image_metadata(self.current_image_path)
                lat, lon, gps_info = self.get_image_location(self.current_image_path)
                
                export_data = {
                    "file_info": {
                        "filename": os.path.basename(self.current_image_path),
                        "filepath": self.current_image_path,
                        "filesize": os.path.getsize(self.current_image_path)
                    },
                    "metadata": metadata,
                    "gps": {
                        "has_gps": lat is not None and lon is not None,
                        "latitude": lat,
                        "longitude": lon,
                        "gps_info": gps_info or {}
                    },
                    "export_info": {
                        "exported_at": datetime.now().isoformat(),
                        "application": "Image Metadata Viewer"
                    }
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "Success", "Metadata exported to JSON successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export JSON: {e}")

    def save_metadata_to_file(self):
        """Save metadata to file"""
        file_path = QFileDialog.getSaveFileName(
            self,
            "Save Metadata",
            "",
            "Text Files (*.txt)"
        )[0]

        if file_path:
            try:
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write("=== Image Metadata ===\n\n")
                    f.write(f"File: {self.current_image_path}\n\n")
                    f.write("=== File Information ===\n")
                    for key, label in [('filename', 'Filename'),
                                      ('filepath', 'File Path'),
                                      ('filesize', 'File Size'),
                                      ('created', 'Created'),
                                      ('modified', 'Modified'),
                                      ('hash', 'MD5 Hash')]:
                        f.write(f"{label}: {self.info_labels[key].text()}\n")

                QMessageBox.information(self, "Success", "Metadata saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save metadata: {e}")

        self.preview_label.clear()
        self.current_image_path = None
        self.current_url = None

    def batch_process(self):
        """Batch process multiple images"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select folder containing images",
            ""
        )
        if not folder_path:
            return

        batch_window = QDialog(self)
        batch_window.setWindowTitle("Batch Processing")
        batch_window.resize(600, 400)

        # Create layout
        layout = QVBoxLayout(batch_window)

        # Create results text area
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        layout.addWidget(results_text)

        # Create progress bar
        progress = QProgressBar()
        layout.addWidget(progress)

        # Create export button
        export_button = QPushButton("Export Results")
        export_button.clicked.connect(lambda: self.export_batch_results(results_text.toPlainText()))
        layout.addWidget(export_button)

        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(batch_window.close)
        layout.addWidget(close_button)

        batch_window.exec_()

        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.bmp']:
            image_files.extend([f for f in os.listdir(folder_path)
                              if f.lower().endswith(ext.replace('*', ''))])

        if not image_files:
            results_text.append("No image files found in the selected folder.")
            return

        progress.setMaximum(len(image_files))
        results_text.append(f"Processing {len(image_files)} images...")

        gps_count = 0
        for i, filename in enumerate(image_files):
            filepath = os.path.join(folder_path, filename)
            try:
                lat, lon, _ = self.get_image_location(filepath)
                has_gps = lat is not None and lon is not None
                if has_gps:
                    gps_count += 1

                results_text.append(
                    f"{filename}: {'✓ GPS' if has_gps else '✗ No GPS'}"
                )

            except Exception as e:
                results_text.append(f"{filename}: Error - {e}")

            progress.setValue(i+1)
            batch_window.show()

        results_text.append(f"\nSummary: {gps_count}/{len(image_files)} images have GPS data")

        def export_batch_results():
            export_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Batch Results",
                os.path.expanduser("~/Desktop"),
                "Text Files (*.txt)"
            )
            if export_path:
                with open(export_path, "w") as f:
                    f.write(results_text.toPlainText())
                QMessageBox.information(self, "Saved", "Batch results saved!")

        export_button.clicked.connect(export_batch_results)

    def compare_images(self):
        """Compare metadata between two images"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select two images to compare",
            "",
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif *.bmp)"
        )

        if len(files) != 2:
            QMessageBox.warning(self, "Warning", "Please select exactly 2 images to compare")
            return

        compare_window = QMainWindow(self)
        compare_window.setWindowTitle("Image Comparison")
        compare_window.resize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        compare_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create table widget
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Property", os.path.basename(files[0]), os.path.basename(files[1]), "Match"])
        
        try:
            metadata1 = self.get_image_metadata(files[0])
            metadata2 = self.get_image_metadata(files[1])

            all_keys = set(metadata1.keys()) | set(metadata2.keys())
            table.setRowCount(len(all_keys))

            for row, key in enumerate(sorted(all_keys)):
                val1 = metadata1.get(key, 'N/A')
                val2 = metadata2.get(key, 'N/A')
                match = "✓" if val1 == val2 else "✗"

                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(val1)[:50]))
                table.setItem(row, 2, QTableWidgetItem(str(val2)[:50]))
                table.setItem(row, 3, QTableWidgetItem(match))

            table.resizeColumnsToContents()
            layout.addWidget(table)
            compare_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compare images: {e}")

    def remove_metadata(self):
        """Remove metadata from an image"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "No image loaded!")
            return

        result = QMessageBox.question(self, "Confirm",
            "This will create a copy of the image without metadata. Continue?")
        if result != QMessageBox.Yes:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save cleaned image as",
            os.path.expanduser("~/Desktop"),
            "JPEG Files (*.jpg);;PNG Files (*.png)"
        )

        if save_path:
            try:
                with Image.open(self.current_image_path) as img:
                    data = list(img.getdata())
                    clean_img = Image.new(img.mode, img.size)
                    clean_img.putdata(data)
                    clean_img.save(save_path)

                QMessageBox.information(self, "Success", "Image saved without metadata!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove metadata: {e}")

    def load_recent_files(self):
        """Load recent files from config"""
        try:
            config_path = os.path.expanduser("~/.image_metadata_viewer_recent.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.recent_files = json.load(f)
            else:
                self.recent_files = []
        except Exception:
            self.recent_files = []
            return False
        return True

    def save_recent_files(self):
        """Save recent files to config"""
        try:
            config_path = os.path.expanduser("~/.image_metadata_viewer_recent.json")
            with open(config_path, 'w') as f:
                json.dump(self.recent_files, f)
            return True
        except Exception:
            return False

    def clear_recent_files(self):
        """Clear recent files list"""
        self.recent_files = []
        if self.save_recent_files():
            self.update_recent_menu()

    def update_recent_menu(self):
        """Update the recent files menu"""
        # Clear existing menu items
        self.recent_menu.clear()
        
        # Add recent files
        for file_path in self.recent_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                action = QAction(f"{filename}", self)
                action.triggered.connect(lambda checked=False, p=file_path: self.open_image(p))
                self.recent_menu.addAction(action)

        # Add separator and clear action if there are recent files
        if self.recent_files:
            self.recent_menu.addSeparator()
            action = QAction("Clear Recent", self)
            action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(action)
        
        # If no recent files, show message
        if not self.recent_files:
            action = QAction("No recent files", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)

    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #333333;
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QPushButton {
                    background-color: #ffffff;
                    color: #000000;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                }
            """)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", """
Enhanced Image Metadata & Location Viewer v2.0

Features:
• View comprehensive image metadata
• Extract and display GPS coordinates
• Support for multiple map services
• Batch processing capabilities
• Image comparison tools
• Metadata removal utility
• Modern tabbed interface
• Dark/Light mode support
• Export to JSON and text formats
• Drag & drop support
• Recent files history
• Modern file dialog

Supported formats: JPEG, PNG, TIFF, BMP, GIF

Created with Python and PyQt5""")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ImageMetadataViewer()
    window.show()
    sys.exit(app.exec_())
