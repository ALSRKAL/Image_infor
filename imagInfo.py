from PIL import Image, ImageTk, ImageEnhance
import os
import sys
import platform
import json
import threading
import requests
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
import customtkinter as ctk
from PIL import Image, ImageTk, ImageEnhance
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from utils import (
    validate_image_file, 
    get_default_save_paths,
    LanguageHandler,
    CacheManager
)
from config import Config

class ImageMetadataViewer:
    def __init__(self, root):
        self.root = root
        self.config = Config()
        self.root.title(self.config.get("app_title", "Image Metadata Viewer"))
        
        # Load system-specific settings
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            self.system_settings = settings['system']
            self.window_settings = settings['window']
            self.appearance = settings['appearance']
            
        # Set system-specific settings
        self.system = platform.system()
        self.current_settings = self.system_settings.get(self.system.lower(), self.system_settings['linux'])
        
        # Set window size
        self.root.geometry(f"{self.window_settings['width']}x{self.window_settings['height']}")
        self.root.minsize(self.window_settings['min_width'], self.window_settings['min_height'])
        
        # Set window icon
        try:
            icon_path = os.path.expanduser(self.current_settings['icon'])
            if os.path.exists(icon_path):
                if self.system == 'Windows':
                    self.root.iconbitmap(icon_path)
                else:
                    self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except:
            pass
            
        # Update file dialog options
        self.file_dialog_options = self.current_settings['file_dialog']
        
        # Initialize components
        self.cache = CacheManager()
        self.lang = LanguageHandler()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        
        # Variables
        self.current_url = None
        self.current_image_path = None
        self.recent_files = []
        self.dark_mode = tk.BooleanVar()
        ctk.set_appearance_mode("light")  # Default to light mode, sync with toggle_dark_mode

        # Load recent files
        self.load_recent_files()

        # Setup UI
        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.setup_drag_drop()

    def setup_styles(self):
        """Setup modern ttk and customtkinter styles"""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configure modern button styles
        self.style.configure("Modern.TButton",
                           padding=(10, 5),
                           font=('Arial', 9))

        # Configure header label style
        self.style.configure("Header.TLabel",
                           font=('Arial', 11, 'bold'),
                           foreground="#2c3e50")

        # Configure customtkinter appearance
        ctk.set_default_color_theme("blue")

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image...", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_separator()

        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self.update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Save Metadata...", command=self.save_metadata_to_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Export as JSON...", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, command=self.toggle_dark_mode)
        view_menu.add_command(label="Refresh", command=self.refresh_current_image, accelerator="F5")

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Batch Process...", command=self.batch_process)
        tools_menu.add_command(label="Compare Images...", command=self.compare_images)
        tools_menu.add_command(label="Remove Metadata...", command=self.remove_metadata)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_image())
        self.root.bind('<Control-s>', lambda e: self.save_metadata_to_file())
        self.root.bind('<F5>', lambda e: self.refresh_current_image())

    def create_widgets(self):
        """Create main widgets"""
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)

        # Right panel for image preview
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        # Toolbar
        self.create_toolbar(left_frame)

        # Notebook for tabbed interface
        notebook = ttk.Notebook(left_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Metadata tab
        metadata_frame = ttk.Frame(notebook)
        notebook.add(metadata_frame, text="📄 Metadata")
        self.create_metadata_tab(metadata_frame)

        # GPS tab
        gps_frame = ttk.Frame(notebook)
        notebook.add(gps_frame, text="🌍 GPS Location")
        self.create_gps_tab(gps_frame)

        # Image Info tab
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="🖼️ Image Info")
        self.create_info_tab(info_frame)

        # Image preview panel
        self.create_preview_panel(right_frame)

        # Status bar
        self.create_status_bar()

    def create_toolbar(self, parent):
        """Create toolbar with buttons"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # File operations
        ttk.Button(toolbar, text="📁 Open", command=self.open_image,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_current_image,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(toolbar, text="🗑️ Clear", command=self.clear_all,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 15))

        # GPS operations
        self.open_maps_button = ttk.Button(toolbar, text="🗺️ Google Maps",
                                          command=self.open_in_google_maps,
                                          state=tk.DISABLED, style="Modern.TButton")
        self.open_maps_button.pack(side=tk.LEFT, padx=(0, 5))

        self.copy_url_button = ttk.Button(toolbar, text="📋 Copy URL",
                                         command=self.copy_url_to_clipboard,
                                         state=tk.DISABLED, style="Modern.TButton")
        self.copy_url_button.pack(side=tk.LEFT, padx=(0, 15))

        # Export operations
        ttk.Button(toolbar, text="💾 Save", command=self.save_metadata_to_file,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(toolbar, text="📊 Export JSON", command=self.export_json,
                  style="Modern.TButton").pack(side=tk.LEFT)

    def create_metadata_tab(self, parent):
        """Create metadata display tab"""
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_metadata)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        # Metadata display with tree view
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for structured metadata display
        self.metadata_tree = ttk.Treeview(tree_frame, columns=('Value',), show='tree headings')
        self.metadata_tree.heading('#0', text='Property')
        self.metadata_tree.heading('Value', text='Value')
        self.metadata_tree.column('#0', width=200)
        self.metadata_tree.column('Value', width=300)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.metadata_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.metadata_tree.xview)
        self.metadata_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.metadata_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Context menu for treeview
        self.create_context_menu()

    def create_gps_tab(self, parent):
        """Create GPS information tab"""
        # GPS info display
        ttk.Label(parent, text="GPS Location Information", style="Header.TLabel").pack(pady=(0, 10))

        self.gps_textbox = scrolledtext.ScrolledText(parent, height=15, font=('Consolas', 10))
        self.gps_textbox.pack(fill=tk.BOTH, expand=True)

        # GPS control buttons
        gps_button_frame = ttk.Frame(parent)
        gps_button_frame.pack(fill=tk.X, pady=(10, 0))

        self.maps_services = [
            ("Google Maps", "https://www.google.com/maps?q={},{}"),
            ("OpenStreetMap", "https://www.openstreetmap.org/?mlat={}&mlon={}"),
            ("Bing Maps", "https://www.bing.com/maps?cp={}~{}")
        ]

        for service_name, _ in self.maps_services:
            btn = ttk.Button(gps_button_frame, text=f"📍 {service_name}",
                           command=lambda sn=service_name: self.open_in_maps(sn),
                           state=tk.DISABLED)
            btn.pack(side=tk.LEFT, padx=(0, 5))
            setattr(self, f"{service_name.lower().replace(' ', '_')}_button", btn)

    def create_info_tab(self, parent):
        """Create image information tab"""
        ttk.Label(parent, text="Image Properties", style="Header.TLabel").pack(pady=(0, 10))

        # Image info frame
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.BOTH, expand=True)

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
            ttk.Label(info_frame, text=label, font=('Arial', 9, 'bold')).grid(
                row=i, column=0, sticky='nw', padx=(0, 10), pady=2)
            self.info_labels[key] = ttk.Label(info_frame, text='-', wraplength=400)
            self.info_labels[key].grid(row=i, column=1, sticky='nw', pady=2)

    def create_preview_panel(self, parent):
        """Create image preview panel"""
        ttk.Label(parent, text="Image Preview", style="Header.TLabel").pack(pady=(0, 10))

        # Preview canvas with scrollbar
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(canvas_frame, bg='white')
        preview_scrollbar_v = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        preview_scrollbar_h = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)

        self.preview_canvas.configure(yscrollcommand=preview_scrollbar_v.set,
                                     xscrollcommand=preview_scrollbar_h.set)

        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        preview_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)

        # Image adjustment controls
        adjust_frame = ttk.LabelFrame(parent, text="Image Adjustments")
        adjust_frame.pack(fill=tk.X, pady=(10, 0))

        # Brightness
        ttk.Label(adjust_frame, text="Brightness:").grid(row=0, column=0, sticky='w')
        self.brightness_var = tk.DoubleVar(value=1.0)
        brightness_scale = ttk.Scale(adjust_frame, from_=0.1, to=2.0,
                                   variable=self.brightness_var,
                                   command=self.adjust_preview)
        brightness_scale.grid(row=0, column=1, sticky='ew', padx=(5, 0))

        # Contrast
        ttk.Label(adjust_frame, text="Contrast:").grid(row=1, column=0, sticky='w')
        self.contrast_var = tk.DoubleVar(value=1.0)
        contrast_scale = ttk.Scale(adjust_frame, from_=0.1, to=2.0,
                                 variable=self.contrast_var,
                                 command=self.adjust_preview)
        contrast_scale.grid(row=1, column=1, sticky='ew', padx=(5, 0))

        adjust_frame.columnconfigure(1, weight=1)

        # Reset button
        ttk.Button(adjust_frame, text="Reset", command=self.reset_adjustments).grid(
            row=2, column=0, columnspan=2, pady=(5, 0))

    def create_status_bar(self):
        """Create status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Drag and drop images or click Open to get started")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_context_menu(self):
        """Create context menu for metadata tree"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Value", command=self.copy_selected_value)
        self.context_menu.add_command(label="Copy Property", command=self.copy_selected_property)

        self.metadata_tree.bind("<Button-3>", self.show_context_menu)

    def setup_drag_drop(self):
        """Setup drag and drop functionality using tkinterdnd2"""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def create_custom_file_dialog(self, title, filetypes, mode="open", initialdir=None):
        """Create a modern custom file dialog using customtkinter"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Variables
        selected_file = tk.StringVar()
        current_dir = initialdir or os.path.expanduser("~/Desktop")

        # Directory navigation
        dir_frame = ctk.CTkFrame(dialog)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)

        dir_entry = ctk.CTkEntry(dir_frame, width=400)
        dir_entry.insert(0, current_dir)
        dir_entry.pack(side=tk.LEFT, padx=5)

        def update_dir():
            new_dir = dir_entry.get()
            if os.path.isdir(new_dir):
                current_dir = new_dir
                update_file_list(current_dir)
            else:
                messagebox.showerror("Error", "Invalid directory")

        ctk.CTkButton(dir_frame, text="Go", command=update_dir).pack(side=tk.LEFT)

        # Quick access buttons
        quick_frame = ctk.CTkFrame(dialog)
        quick_frame.pack(fill=tk.X, padx=10, pady=5)

        def set_dir(path):
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, path)
            update_dir()

        ctk.CTkButton(quick_frame, text="Desktop", command=lambda: set_dir(os.path.expanduser("~/Desktop"))).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(quick_frame, text="Downloads", command=lambda: set_dir(os.path.expanduser("~/Downloads"))).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(quick_frame, text="Documents", command=lambda: set_dir(os.path.expanduser("~/Documents"))).pack(side=tk.LEFT, padx=5)

        # File list
        file_frame = ctk.CTkFrame(dialog)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        file_tree = ttk.Treeview(file_frame, columns=("Name", "Type"), show="tree headings")
        file_tree.heading("Name", text="Name")
        file_tree.heading("Type", text="Type")
        file_tree.column("Name", width=300)
        file_tree.column("Type", width=100)
        vsb = ttk.Scrollbar(file_frame, orient="vertical", command=file_tree.yview)
        file_tree.configure(yscrollcommand=vsb.set)
        file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        def update_file_list(directory):
            for item in file_tree.get_children():
                file_tree.delete(item)
            try:
                for item in os.listdir(directory):
                    full_path = os.path.join(directory, item)
                    item_type = "Folder" if os.path.isdir(full_path) else "File"
                    if item_type == "File" and mode == "open":
                        if not any(item.lower().endswith(ext[1].split()[-1].replace("*.", ".")) for ext in filetypes):
                            continue
                    file_tree.insert("", "end", text=item, values=(item, item_type))
            except Exception as e:
                messagebox.showerror("Error", f"Cannot access directory: {e}")

        def on_select(event):
            selected = file_tree.selection()
            if selected:
                item = file_tree.item(selected[0])["text"]
                full_path = os.path.join(dir_entry.get(), item)
                if os.path.isdir(full_path):
                    dir_entry.delete(0, tk.END)
                    dir_entry.insert(0, full_path)
                    update_file_list(full_path)
                elif os.path.isfile(full_path):
                    selected_file.set(full_path)

        def on_double_click(event):
            selected = file_tree.selection()
            if selected:
                item = file_tree.item(selected[0])["text"]
                full_path = os.path.join(dir_entry.get(), item)
                if os.path.isfile(full_path):
                    selected_file.set(full_path)
                    dialog.destroy()

        file_tree.bind("<<TreeviewSelect>>", on_select)
        file_tree.bind("<Double-1>", on_double_click)

        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        def confirm():
            if selected_file.get():
                dialog.destroy()
            elif mode == "save":
                selected_file.set(os.path.join(dir_entry.get(), filename_entry.get()))
                dialog.destroy()

        ctk.CTkButton(button_frame, text="Select", command=confirm).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        if mode == "save":
            filename_entry = ctk.CTkEntry(button_frame, placeholder_text="Enter filename")
            filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        update_file_list(current_dir)

        dialog.wait_window()
        return selected_file.get()

    def handle_drop(self, event):
        """Handle dropped files"""
        files = self.root.splitlist(event.data)
        if files:
            self.load_image(files[0])

    def get_image_metadata(self, image_path):
        """Extract metadata from image"""
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
            messagebox.showerror("Error", f"Error reading metadata: {e}")
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
            messagebox.showerror("Error", f"Error reading GPS data: {e}")
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
        file_path = self.create_custom_file_dialog(
            title="Select an Image",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif"),
                ("JPEG Files", "*.jpg *.jpeg"),
                ("PNG Files", "*.png"),
                ("TIFF Files", "*.tiff *.tif"),
                ("All Files", "*.*")
            ],
            initialdir=os.path.expanduser("~/Desktop")
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        """Load and analyze image"""
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File not found!")
            return

        self.status_var.set("Loading image...")
        self.root.update_idletasks()

        self.current_image_path = file_path

        # Add to recent files
        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
            self.recent_files = self.recent_files[:10]
            self.save_recent_files()
            self.update_recent_menu()

        # Load metadata
        metadata = self.get_image_metadata(file_path)
        self.display_metadata(metadata)

        # Load GPS info
        lat, lon, gps_info = self.get_image_location(file_path)
        self.display_gps_info(lat, lon, gps_info)

        # Load image info
        self.display_image_info(file_path)

        # Load preview
        self.load_preview(file_path)

        self.status_var.set(f"Loaded: {os.path.basename(file_path)}")

    def display_metadata(self, metadata):
        """Display metadata in tree view"""
        for item in self.metadata_tree.get_children():
            self.metadata_tree.delete(item)

        if not metadata:
            self.metadata_tree.insert('', 'end', text='No metadata found', values=('',))
            return

        categories = {
            'Basic': ['ImageWidth', 'ImageLength', 'Make', 'Model', 'Software'],
            'Camera': ['FNumber', 'ExposureTime', 'ISOSpeedRatings', 'FocalLength', 'Flash'],
            'DateTime': ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized'],
            'Other': []
        }

        categorized = {cat: {} for cat in categories}
        uncategorized = {}

        for key, value in metadata.items():
            placed = False
            for cat, keys in categories.items():
                if key in keys:
                    categorized[cat][key] = value
                    placed = True
                    break
            if not placed:
                uncategorized[key] = value

        categorized['Other'] = uncategorized

        for category, items in categorized.items():
            if items:
                cat_item = self.metadata_tree.insert('', 'end', text=f'📁 {category}', values=('',))
                for key, value in items.items():
                    self.metadata_tree.insert(cat_item, 'end', text=key, values=(str(value)[:100],))

    def display_gps_info(self, lat, lon, gps_info):
        """Display GPS information"""
        self.gps_textbox.delete(1.0, tk.END)

        if lat is not None and lon is not None:
            gps_text = f"📍 GPS Coordinates Found!\n\n"
            gps_text += f"Latitude: {lat:.6f}°\n"
            gps_text += f"Longitude: {lon:.6f}°\n\n"
            gps_text += f"Decimal Degrees: {lat:.6f}, {lon:.6f}\n\n"

            if gps_info:
                gps_text += "Additional GPS Data:\n"
                for key, value in gps_info.items():
                    tag_name = GPSTAGS.get(key, f"GPS_{key}")
                    gps_text += f"{tag_name}: {value}\n"

            for service_name, _ in self.maps_services:
                btn_name = f"{service_name.lower().replace(' ', '_')}_button"
                if hasattr(self, btn_name):
                    getattr(self, btn_name).config(state=tk.NORMAL)

            self.open_maps_button.config(state=tk.NORMAL)
            self.copy_url_button.config(state=tk.NORMAL)

            self.current_lat = lat
            self.current_lon = lon
            self.current_url = f"https://www.google.com/maps?q={lat},{lon}"

        else:
            gps_text = "❌ No GPS data found in this image.\n\n"
            gps_text += "GPS coordinates are typically embedded in photos taken with:\n"
            gps_text += "• Smartphones with location services enabled\n"
            gps_text += "• Cameras with built-in GPS\n"
            gps_text += "• Images geotagged manually\n"

            for service_name, _ in self.maps_services:
                btn_name = f"{service_name.lower().replace(' ', '_')}_button"
                if hasattr(self, btn_name):
                    getattr(self, btn_name).config(state=tk.DISABLED)

            self.open_maps_button.config(state=tk.DISABLED)
            self.copy_url_button.config(state=tk.DISABLED)

        self.gps_textbox.insert(tk.END, gps_text)

    def display_image_info(self, file_path):
        """Display image file information"""
        try:
            stat = os.stat(file_path)
            self.info_labels['filename'].config(text=os.path.basename(file_path))
            self.info_labels['filepath'].config(text=file_path)
            self.info_labels['filesize'].config(text=f"{stat.st_size:,} bytes ({stat.st_size/1024/1024:.2f} MB)")
            self.info_labels['created'].config(text=datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'))
            self.info_labels['modified'].config(text=datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))

            with Image.open(file_path) as img:
                self.info_labels['dimensions'].config(text=f"{img.width} × {img.height} pixels")
                self.info_labels['format'].config(text=img.format or 'Unknown')
                self.info_labels['mode'].config(text=img.mode)

            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            self.info_labels['hash'].config(text=hash_md5.hexdigest())

        except Exception as e:
            for label in self.info_labels.values():
                label.config(text='Error')

    def load_preview(self, file_path):
        """Load image preview"""
        try:
            self.original_image = Image.open(file_path)
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preview: {e}")

    def update_preview(self):
        """Update preview with current adjustments"""
        if not hasattr(self, 'original_image'):
            return

        try:
            img = self.original_image.copy()

            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.brightness_var.get())

            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.contrast_var.get())

            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(img)

            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                self.preview_canvas.winfo_width()//2,
                self.preview_canvas.winfo_height()//2,
                image=self.preview_photo,
                anchor=tk.CENTER
            )

            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

        except Exception as e:
            print(f"Preview update error: {e}")

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

    def open_in_maps(self, service_name):
        """Open location in specified map service"""
        if hasattr(self, 'current_lat') and hasattr(self, 'current_lon'):
            url_template = next(url for name, url in self.maps_services if name == service_name)
            url = url_template.format(self.current_lat, self.current_lon)
            webbrowser.open(url)

    def copy_url_to_clipboard(self):
        """Copy URL to clipboard"""
        if self.current_url:
            pyperclip.copy(self.current_url)
            messagebox.showinfo("Copied", "Google Maps URL copied to clipboard!")

    def copy_selected_value(self):
        """Copy selected metadata value"""
        selection = self.metadata_tree.selection()
        if selection:
            item = selection[0]
            value = self.metadata_tree.item(item)['values'][0]
            pyperclip.copy(str(value))
            messagebox.showinfo("Copied", "Value copied to clipboard!")

    def copy_selected_property(self):
        """Copy selected metadata property name"""
        selection = self.metadata_tree.selection()
        if selection:
            item = selection[0]
            property_name = self.metadata_tree.item(item)['text']
            pyperclip.copy(property_name)
            messagebox.showinfo("Copied", "Property name copied to clipboard!")

    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def clear_all(self):
        """Clear all data"""
        for item in self.metadata_tree.get_children():
            self.metadata_tree.delete(item)

        self.gps_textbox.delete(1.0, tk.END)

        for label in self.info_labels.values():
            label.config(text='-')

        self.preview_canvas.delete("all")

        self.current_image_path = None
        self.current_url = None

        self.open_maps_button.config(state=tk.DISABLED)
        self.copy_url_button.config(state=tk.DISABLED)
        for service_name, _ in self.maps_services:
            btn_name = f"{service_name.lower().replace(' ', '_')}_button"
            if hasattr(self, btn_name):
                getattr(self, btn_name).config(state=tk.DISABLED)

        self.reset_adjustments()

        self.status_var.set("Ready")

    def refresh_current_image(self):
        """Refresh current image"""
        if self.current_image_path and os.path.exists(self.current_image_path):
            self.load_image(self.current_image_path)
        else:
            messagebox.showwarning("Warning", "No image loaded or file not found!")

    def save_metadata_to_file(self):
        """Save metadata to file with modern dialog"""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        file_path = self.create_custom_file_dialog(
            title="Save Metadata",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            mode="save",
            initialdir=os.path.expanduser("~/Desktop")
        )

        if file_path:
            try:
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(f"Image Metadata Report\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Source: {self.current_image_path}\n")
                    f.write("="*50 + "\n\n")

                    f.write("METADATA:\n")
                    f.write("-"*20 + "\n")
                    metadata = self.get_image_metadata(self.current_image_path)
                    for key, value in metadata.items():
                        f.write(f"{key}: {value}\n")

                    f.write(f"\nGPS INFORMATION:\n")
                    f.write("-"*20 + "\n")
                    gps_content = self.gps_textbox.get(1.0, tk.END)
                    f.write(gps_content)

                    f.write(f"\nIMAGE INFORMATION:\n")
                    f.write("-"*20 + "\n")
                    for key, label in [('filename', 'Filename'), ('filepath', 'File Path'),
                                     ('filesize', 'File Size'), ('dimensions', 'Dimensions'),
                                     ('format', 'Format'), ('mode', 'Color Mode'),
                                     ('created', 'Created'), ('modified', 'Modified'),
                                     ('hash', 'MD5 Hash')]:
                        f.write(f"{label}: {self.info_labels[key].cget('text')}\n")

                messagebox.showinfo("Success", "Metadata saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save metadata: {e}")

    def export_json(self):
        """Export metadata as JSON with modern dialog"""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        file_path = self.create_custom_file_dialog(
            title="Export as JSON",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            mode="save",
            initialdir=os.path.expanduser("~/Desktop")
        )

        if file_path:
            try:
                metadata = self.get_image_metadata(self.current_image_path)
                lat, lon, gps_info = self.get_image_location(self.current_image_path)

                export_data = {
                    "export_info": {
                        "generated": datetime.now().isoformat(),
                        "source_file": self.current_image_path,
                        "tool": "Enhanced Image Metadata Viewer"
                    },
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
                        "raw_gps_info": {str(k): str(v) for k, v in gps_info.items()} if gps_info else {}
                    }
                }

                with open(file_path, "w", encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", "Data exported as JSON successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export JSON: {e}")

    def batch_process(self):
        """Batch process multiple images"""
        folder_path = filedialog.askdirectory(title="Select folder containing images")
        if not folder_path:
            return

        batch_window = tk.Toplevel(self.root)
        batch_window.title("Batch Processing")
        batch_window.geometry("600x400")

        ttk.Label(batch_window, text="Batch Processing Results",
                 style="Header.TLabel").pack(pady=10)

        results_text = scrolledtext.ScrolledText(batch_window, height=20)
        results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        progress = ttk.Progressbar(batch_window, mode='determinate')
        progress.pack(fill=tk.X, padx=10, pady=(0, 10))

        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.bmp']:
            image_files.extend([f for f in os.listdir(folder_path)
                              if f.lower().endswith(ext.replace('*', ''))])

        if not image_files:
            results_text.insert(tk.END, "No image files found in the selected folder.\n")
            return

        progress.config(maximum=len(image_files))
        results_text.insert(tk.END, f"Processing {len(image_files)} images...\n\n")

        gps_count = 0
        for i, filename in enumerate(image_files):
            filepath = os.path.join(folder_path, filename)
            try:
                lat, lon, _ = self.get_image_location(filepath)
                has_gps = lat is not None and lon is not None
                if has_gps:
                    gps_count += 1

                results_text.insert(tk.END,
                    f"{filename}: {'✓ GPS' if has_gps else '✗ No GPS'}\n")

            except Exception as e:
                results_text.insert(tk.END, f"{filename}: Error - {e}\n")

            progress.config(value=i+1)
            batch_window.update_idletasks()

        results_text.insert(tk.END, f"\nSummary: {gps_count}/{len(image_files)} images have GPS data")

        def export_batch_results():
            export_path = self.create_custom_file_dialog(
                title="Save Batch Results",
                filetypes=[("Text Files", "*.txt")],
                mode="save",
                initialdir=os.path.expanduser("~/Desktop")
            )
            if export_path:
                with open(export_path, "w") as f:
                    f.write(results_text.get(1.0, tk.END))
                messagebox.showinfo("Saved", "Batch results saved!")

        ttk.Button(batch_window, text="Export Results",
                  command=export_batch_results).pack(pady=5)

    def compare_images(self):
        """Compare metadata between two images"""
        files = filedialog.askopenfilenames(
            title="Select two images to compare",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp")]
        )

        if len(files) != 2:
            messagebox.showwarning("Warning", "Please select exactly 2 images to compare")
            return

        compare_window = tk.Toplevel(self.root)
        compare_window.title("Image Comparison")
        compare_window.geometry("800x600")

        notebook = ttk.Notebook(compare_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        metadata_frame = ttk.Frame(notebook)
        notebook.add(metadata_frame, text="Metadata Comparison")

        compare_tree = ttk.Treeview(metadata_frame,
                                   columns=('Image1', 'Image2', 'Match'),
                                   show='tree headings')
        compare_tree.heading('#0', text='Property')
        compare_tree.heading('Image1', text=os.path.basename(files[0]))
        compare_tree.heading('Image2', text=os.path.basename(files[1]))
        compare_tree.heading('Match', text='Match')

        compare_tree.pack(fill=tk.BOTH, expand=True)

        try:
            metadata1 = self.get_image_metadata(files[0])
            metadata2 = self.get_image_metadata(files[1])

            all_keys = set(metadata1.keys()) | set(metadata2.keys())

            for key in sorted(all_keys):
                val1 = metadata1.get(key, 'N/A')
                val2 = metadata2.get(key, 'N/A')
                match = "✓" if val1 == val2 else "✗"

                compare_tree.insert('', 'end', text=key,
                                   values=(str(val1)[:50], str(val2)[:50], match))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to compare images: {e}")

    def remove_metadata(self):
        """Remove metadata from an image"""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        result = messagebox.askyesno("Confirm",
            "This will create a copy of the image without metadata. Continue?")
        if not result:
            return

        save_path = self.create_custom_file_dialog(
            title="Save cleaned image as",
            filetypes=[("JPEG Files", "*.jpg"), ("PNG Files", "*.png")],
            mode="save",
            initialdir=os.path.expanduser("~/Desktop")
        )

        if save_path:
            try:
                with Image.open(self.current_image_path) as img:
                    data = list(img.getdata())
                    clean_img = Image.new(img.mode, img.size)
                    clean_img.putdata(data)
                    clean_img.save(save_path)

                messagebox.showinfo("Success", "Image saved without metadata!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove metadata: {e}")

    def load_recent_files(self):
        """Load recent files from config"""
        try:
            config_path = os.path.expanduser("~/.image_metadata_viewer_recent.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.recent_files = json.load(f)
            else:
                self.recent_files = []
        except:
            self.recent_files = []

    def save_recent_files(self):
        """Save recent files to config"""
        try:
            config_path = os.path.expanduser("~/.image_metadata_viewer_recent.json")
            with open(config_path, 'w') as f:
                json.dump(self.recent_files, f)
        except:
            pass

    def update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.delete(0, tk.END)

        if not self.recent_files:
            self.recent_menu.add_command(label="No recent files", state=tk.DISABLED)
        else:
            for i, filepath in enumerate(self.recent_files[:10]):
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    self.recent_menu.add_command(
                        label=f"{i+1}. {filename}",
                        command=lambda fp=filepath: self.load_image(fp)
                    )

            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent", command=self.clear_recent_files)

    def clear_recent_files(self):
        """Clear recent files list"""
        self.recent_files = []
        self.save_recent_files()
        self.update_recent_menu()

    def toggle_dark_mode(self):
        """Toggle dark mode for both ttk and customtkinter"""
        if self.dark_mode.get():
            bg_color = "#2d2d2d"
            fg_color = "#ffffff"
            select_bg = "#404040"
            ctk.set_appearance_mode("dark")
        else:
            bg_color = "#ffffff"
            fg_color = "#000000"
            ctk.set_appearance_mode("light")

        self.root.tk_setPalette(background=bg_color, foreground=fg_color,
                               selectBackground=select_bg)
        self.gps_textbox.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.preview_canvas.config(bg="#1a1a1a" if self.dark_mode.get() else "white")
        self.style.configure("Treeview", background=bg_color, foreground=fg_color,
                           fieldbackground=bg_color)
        self.style.configure("Treeview.Heading", background="#404040" if self.dark_mode.get() else "#f0f0f0",
                           foreground=fg_color)

    def show_about(self):
        """Show about dialog"""
        about_text = """Enhanced Image Metadata & Location Viewer v2.0

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

Created with Python, Tkinter, and CustomTkinter"""

        messagebox.showinfo("About", about_text)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageMetadataViewer(root)
    root.mainloop()
