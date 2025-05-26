#!/usr/bin/env python3
"""
ExifTool GUI - A modern macOS application for editing metadata
Author: Your Name
License: MIT
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from PIL import Image, ImageTk
import platform
import mimetypes
from collections import defaultdict

# Custom modern colors
COLORS = {
    'bg_primary': '#1a1a1a',
    'bg_secondary': '#2a2a2a',
    'bg_tertiary': '#3a3a3a',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'accent': '#007AFF',  # macOS blue
    'accent_hover': '#0051D5',
    'success': '#32D74B',
    'warning': '#FF9500',
    'error': '#FF3B30',
    'border': '#404040',
    'modified': '#FF9500',
    'tag_bg': '#2a2a2a',
    'tag_hover': '#3a3a3a'
}

# File type categories and icons
FILE_CATEGORIES = {
    'Images': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.heic', '.heif'],
        'icon': '🖼️',
        'raw_formats': ['.raw', '.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.rw2', '.raf', '.srw']
    },
    'Videos': {
        'extensions': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'],
        'icon': '🎬'
    },
    'Audio': {
        'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.aiff', '.ape'],
        'icon': '🎵'
    },
    'Documents': {
        'extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods'],
        'icon': '📄'
    },
    'Archives': {
        'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
        'icon': '📦'
    }
}

class ModernButton(tk.Button):
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        self.style = style
        super().__init__(parent, text=text, command=command, **kwargs)
        self.configure(
            relief=tk.FLAT,
            cursor="hand2",
            font=("SF Pro Display", 11),
            padx=16,
            pady=8,
            borderwidth=0,
            highlightthickness=0
        )
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.set_style()
    
    def set_style(self):
        if self.style == "primary":
            self.configure(
                bg=COLORS['accent'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_hover'],
                activeforeground=COLORS['text_primary']
            )
        elif self.style == "secondary":
            self.configure(
                bg=COLORS['bg_tertiary'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['border'],
                activeforeground=COLORS['text_primary']
            )
    
    def on_hover(self, event):
        if self.style == "primary":
            self.configure(bg=COLORS['accent_hover'])
        else:
            self.configure(bg=COLORS['border'])
    
    def on_leave(self, event):
        self.set_style()

class ModernEntry(tk.Entry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            font=("SF Pro Display", 11),
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )

class ModernTreeview(ttk.Treeview):
    def __init__(self, parent, **kwargs):
        # Create custom style
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure the Treeview style
        style.configure("Modern.Treeview",
            background=COLORS['bg_secondary'],
            foreground=COLORS['text_primary'],
            fieldbackground=COLORS['bg_secondary'],
            borderwidth=0,
            font=("SF Pro Display", 11)
        )
        
        style.configure("Modern.Treeview.Heading",
            background=COLORS['bg_primary'],
            foreground=COLORS['text_primary'],
            borderwidth=0,
            font=("SF Pro Display", 12, "bold")
        )
        
        style.map("Modern.Treeview",
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', COLORS['text_primary'])]
        )
        
        super().__init__(parent, style="Modern.Treeview", **kwargs)

class ExifToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ExifTool GUI")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Configure root window
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Set window to dark mode on macOS
        if platform.system() == 'Darwin':
            try:
                from ctypes import c_void_p, c_char_p, cdll
                libobjc = cdll.LoadLibrary('libobjc.dylib')
                NSString = libobjc.objc_getClass(b'NSString')
                ns_app = libobjc.objc_getClass(b'NSApplication').sharedApplication()
                ns_app.setAppearance_(libobjc.objc_msgSend(
                    libobjc.objc_getClass(b'NSAppearance'),
                    libobjc.sel_registerName(b'appearanceNamed:'),
                    NSString.stringWithUTF8String_(b'NSAppearanceNameVibrantDark')
                ))
            except:
                pass
        
        self.current_file = None
        self.metadata = {}
        self.modified_fields = set()
        self.file_type = None
        self.clipboard_data = {}
        
        # Check for exiftool
        self.exiftool_path = self.find_exiftool()
        if not self.exiftool_path:
            messagebox.showerror("Error", "ExifTool not found. Please install it first.")
            sys.exit(1)
        
        self.setup_ui()
        
    def find_exiftool(self):
        """Find exiftool in system PATH or common locations"""
        if shutil.which('exiftool'):
            return 'exiftool'
        
        common_paths = [
            '/usr/local/bin/exiftool',
            '/opt/homebrew/bin/exiftool',
            '/usr/bin/exiftool'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def get_file_category(self, filename):
        """Determine file category based on extension"""
        ext = Path(filename).suffix.lower()
        
        for category, info in FILE_CATEGORIES.items():
            if ext in info['extensions']:
                return category, info['icon']
            if 'raw_formats' in info and ext in info['raw_formats']:
                return category, info['icon']
        
        return 'Other', '📎'
    
    def setup_ui(self):
        """Setup the modern UI"""
        # Create custom menu bar
        self.create_menu_bar()
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top toolbar
        toolbar = tk.Frame(main_container, bg=COLORS['bg_primary'], height=50)
        toolbar.pack(fill=tk.X, pady=(0, 20))
        
        # File info section
        file_info_frame = tk.Frame(toolbar, bg=COLORS['bg_secondary'])
        file_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # File icon and name
        self.file_icon_label = tk.Label(file_info_frame, text="📁", font=("SF Pro Display", 24), 
                                       bg=COLORS['bg_secondary'], fg=COLORS['text_primary'])
        self.file_icon_label.pack(side=tk.LEFT, padx=15)
        
        file_details = tk.Frame(file_info_frame, bg=COLORS['bg_secondary'])
        file_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
        
        self.file_name_label = tk.Label(file_details, text="No file selected", 
                                       font=("SF Pro Display", 14, "bold"),
                                       bg=COLORS['bg_secondary'], fg=COLORS['text_primary'])
        self.file_name_label.pack(anchor=tk.W)
        
        self.file_info_label = tk.Label(file_details, text="Drop a file or click to browse", 
                                       font=("SF Pro Display", 11),
                                       bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'])
        self.file_info_label.pack(anchor=tk.W)
        
        # Action buttons
        button_frame = tk.Frame(toolbar, bg=COLORS['bg_primary'])
        button_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        ModernButton(button_frame, text="Open File", command=self.open_file, 
                    style="secondary").pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ModernButton(button_frame, text="Save Changes", command=self.save_changes, 
                                    style="primary")
        self.save_btn.pack(side=tk.LEFT)
        self.save_btn.configure(state=tk.DISABLED)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create paned window for resizable panels
        paned = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL, 
                              bg=COLORS['bg_primary'], bd=0, sashwidth=8,
                              sashrelief=tk.FLAT, showhandle=False)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Preview
        left_panel = tk.Frame(paned, bg=COLORS['bg_secondary'])
        paned.add(left_panel, minsize=300)
        
        preview_header = tk.Frame(left_panel, bg=COLORS['bg_secondary'], height=40)
        preview_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(preview_header, text="Preview", font=("SF Pro Display", 14, "bold"),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(side=tk.LEFT)
        
        # Preview area
        self.preview_frame = tk.Frame(left_panel, bg=COLORS['bg_tertiary'])
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.preview_label = tk.Label(self.preview_frame, text="No preview available", 
                                     font=("SF Pro Display", 12),
                                     bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
        self.preview_label.pack(expand=True)
        
        # Right panel - Metadata
        right_panel = tk.Frame(paned, bg=COLORS['bg_secondary'])
        paned.add(right_panel, minsize=400)
        
        # Metadata header with search
        metadata_header = tk.Frame(right_panel, bg=COLORS['bg_secondary'], height=40)
        metadata_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(metadata_header, text="Metadata", font=("SF Pro Display", 14, "bold"),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(side=tk.LEFT)
        
        # Search box
        search_frame = tk.Frame(metadata_header, bg=COLORS['bg_tertiary'])
        search_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        search_icon = tk.Label(search_frame, text="🔍", font=("SF Pro Display", 12),
                              bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
        search_icon.pack(side=tk.LEFT, padx=(10, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_metadata)
        search_entry = ModernEntry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        # Metadata treeview
        tree_frame = tk.Frame(right_panel, bg=COLORS['bg_secondary'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Create treeview with scrollbars
        tree_container = tk.Frame(tree_frame, bg=COLORS['bg_secondary'])
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ModernTreeview(tree_container, columns=('Value',), height=20)
        self.tree.heading('#0', text='Tag', anchor=tk.W)
        self.tree.heading('Value', text='Value', anchor=tk.W)
        self.tree.column('#0', width=350)
        self.tree.column('Value', width=400)
        
        # Modern scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Tag configuration for modified items
        self.tree.tag_configure('modified', foreground=COLORS['modified'])
        self.tree.tag_configure('category', font=("SF Pro Display", 12, "bold"))
        
        # Double-click to edit
        self.tree.bind('<Double-Button-1>', self.edit_tag)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg=COLORS['bg_tertiary'], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=("SF Pro Display", 10),
                               bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
        status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Keyboard shortcuts
        self.root.bind('<Command-o>', lambda e: self.open_file())
        self.root.bind('<Command-s>', lambda e: self.save_changes())
        self.root.bind('<Command-f>', lambda e: search_entry.focus())
        
        # Drag and drop support
        self.root.bind('<Button-1>', self.on_click)
        self.setup_drag_drop()
    
    def create_menu_bar(self):
        """Create custom menu bar"""
        menubar = tk.Menu(self.root, bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                         activebackground=COLORS['accent'], activeforeground=COLORS['text_primary'])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                           activebackground=COLORS['accent'], activeforeground=COLORS['text_primary'])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="⌘O")
        file_menu.add_command(label="Save", command=self.save_changes, accelerator="⌘S")
        file_menu.add_separator()
        file_menu.add_command(label="Export Metadata...", command=self.export_metadata)
        file_menu.add_command(label="Import Metadata...", command=self.import_metadata)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit, accelerator="⌘Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                           activebackground=COLORS['accent'], activeforeground=COLORS['text_primary'])
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy All Tags", command=self.copy_all_tags, accelerator="⌘C")
        edit_menu.add_command(label="Paste Tags", command=self.paste_tags, accelerator="⌘V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", command=lambda: self.search_var.set(""), accelerator="⌘F")
        edit_menu.add_separator()
        edit_menu.add_command(label="Remove All Tags", command=self.remove_all_tags)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                            activebackground=COLORS['accent'], activeforeground=COLORS['text_primary'])
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Batch Process...", command=self.batch_process)
        tools_menu.add_command(label="Date/Time Shift...", command=self.datetime_shift)
        tools_menu.add_command(label="Template Manager...", command=self.template_manager)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                           activebackground=COLORS['accent'], activeforeground=COLORS['text_primary'])
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Expand All", command=lambda: self.expand_all())
        view_menu.add_command(label="Collapse All", command=lambda: self.collapse_all())
        view_menu.add_separator()
        view_menu.add_command(label="Show Only Modified", command=self.show_modified_only)
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        # This is a simplified version - for full drag and drop support,
        # you would need to use tkdnd2 or similar library
        self.root.bind('<Button-1>', self.on_click)
    
    def on_click(self, event):
        """Handle click events for drag and drop simulation"""
        # Simplified drag and drop - in production, use proper drag and drop library
        pass
    
    def open_file(self):
        """Open a file and load its metadata"""
        # Create file type filter string
        all_extensions = []
        filetypes = [("All supported files", "*.*")]
        
        for category, info in FILE_CATEGORIES.items():
            extensions = info['extensions'] + info.get('raw_formats', [])
            all_extensions.extend(extensions)
            ext_string = " ".join([f"*{ext}" for ext in extensions])
            filetypes.append((f"{category} files", ext_string))
        
        filename = filedialog.askopenfilename(
            title="Select File",
            filetypes=filetypes
        )
        
        if filename:
            self.load_file(filename)
    
    def load_file(self, filename):
        """Load a file and its metadata"""
        self.current_file = filename
        self.modified_fields.clear()
        
        # Update file info
        file_path = Path(filename)
        self.file_name_label.config(text=file_path.name)
        
        # Get file info
        file_size = file_path.stat().st_size
        size_str = self.format_file_size(file_size)
        category, icon = self.get_file_category(filename)
        self.file_type = category
        
        self.file_icon_label.config(text=icon)
        self.file_info_label.config(text=f"{category} • {size_str}")
        
        # Load metadata
        self.load_metadata()
        
        # Load preview
        self.load_preview()
        
        # Enable save button
        self.save_btn.configure(state=tk.NORMAL)
        
        self.status_var.set(f"Loaded: {file_path.name}")
    
    def format_file_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def load_metadata(self):
        """Load metadata using exiftool"""
        if not self.current_file:
            return
        
        try:
            # Run exiftool with JSON output
            cmd = [self.exiftool_path, '-j', '-G', '-s', self.current_file]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                data = json.loads(result.stdout)[0]
                self.metadata = data
                self.display_metadata()
            else:
                messagebox.showerror("Error", f"Failed to read metadata: {result.stderr}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read metadata: {str(e)}")
    
    def display_metadata(self):
        """Display metadata in the treeview with modern styling"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Group tags by category
        categories = defaultdict(list)
        for key, value in self.metadata.items():
            if ':' in key:
                category, tag = key.split(':', 1)
            else:
                category = 'File'
                tag = key
            
            categories[category].append((tag, value, key))
        
        # Add to treeview with icons
        category_icons = {
            'EXIF': '📸',
            'File': '📄',
            'IPTC': '📝',
            'XMP': '🏷️',
            'Composite': '🔧',
            'Audio': '🎵',
            'Video': '🎬',
            'QuickTime': '🎬',
            'ID3': '🎵',
            'Vorbis': '🎵'
        }
        
        for category in sorted(categories.keys()):
            icon = category_icons.get(category, '📋')
            parent = self.tree.insert('', 'end', text=f"{icon} {category}", open=True, tags=('category',))
            
            for tag, value, full_key in sorted(categories[category]):
                # Format value for display
                if isinstance(value, (list, dict)):
                    display_value = json.dumps(value, ensure_ascii=False)
                else:
                    display_value = str(value)
                
                # Truncate long values
                if len(display_value) > 100:
                    display_value = display_value[:97] + "..."
                
                # Check if modified
                tags = ('modified',) if full_key in self.modified_fields else ()
                self.tree.insert(parent, 'end', text=tag, values=(display_value,), tags=tags)
    
    def filter_metadata(self, *args):
        """Filter displayed metadata based on search"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.display_metadata()
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Group and filter tags
        categories = defaultdict(list)
        for key, value in self.metadata.items():
            if search_term in key.lower() or search_term in str(value).lower():
                if ':' in key:
                    category, tag = key.split(':', 1)
                else:
                    category = 'File'
                    tag = key
                
                categories[category].append((tag, value, key))
        
        # Add filtered results
        for category in sorted(categories.keys()):
            if categories[category]:
                parent = self.tree.insert('', 'end', text=category, open=True, tags=('category',))
                for tag, value, full_key in sorted(categories[category]):
                    display_value = str(value)
                    if len(display_value) > 100:
                        display_value = display_value[:97] + "..."
                    
                    tags = ('modified',) if full_key in self.modified_fields else ()
                    self.tree.insert(parent, 'end', text=tag, values=(display_value,), tags=tags)
    
    def load_preview(self):
        """Load and display preview based on file type"""
        if not self.current_file:
            return
        
        # Clear previous preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        try:
            if self.file_type == "Images":
                self.load_image_preview()
            elif self.file_type == "Audio":
                self.load_audio_preview()
            elif self.file_type == "Videos":
                self.load_video_preview()
            elif self.file_type == "Documents":
                self.load_document_preview()
            else:
                self.load_generic_preview()
        except Exception as e:
            self.show_preview_error(str(e))
    
    def load_image_preview(self):
        """Load image preview"""
        try:
            # Load image
            image = Image.open(self.current_file)
            
            # Get EXIF orientation
            exif = image.getexif()
            orientation = exif.get(0x0112, 1)
            
            # Rotate based on EXIF orientation
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
            
            # Calculate size to fit in preview area
            preview_width = self.preview_frame.winfo_width() or 400
            preview_height = self.preview_frame.winfo_height() or 400
            
            # Resize maintaining aspect ratio
            image.thumbnail((preview_width - 40, preview_height - 40), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Create label with image
            image_label = tk.Label(self.preview_frame, image=photo, 
                                  bg=COLORS['bg_tertiary'])
            image_label.image = photo  # Keep a reference
            image_label.pack(expand=True)
            
            # Add image info
            info_text = f"{image.width}×{image.height} • {image.mode}"
            info_label = tk.Label(self.preview_frame, text=info_text,
                                 font=("SF Pro Display", 10),
                                 bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
            info_label.pack(pady=(10, 0))
            
        except Exception as e:
            self.show_preview_error(f"Cannot load image: {str(e)}")
    
    def load_audio_preview(self):
        """Load audio file preview"""
        # Create audio preview UI
        preview_container = tk.Frame(self.preview_frame, bg=COLORS['bg_tertiary'])
        preview_container.pack(expand=True)
        
        # Large audio icon
        icon_label = tk.Label(preview_container, text="🎵", font=("SF Pro Display", 72),
                             bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'])
        icon_label.pack(pady=(0, 20))
        
        # Get audio metadata
        audio_info = []
        
        # Extract relevant audio metadata
        duration = self.metadata.get('Duration', 'Unknown')
        bitrate = self.metadata.get('AudioBitrate', self.metadata.get('Bitrate', 'Unknown'))
        sample_rate = self.metadata.get('AudioSampleRate', self.metadata.get('SampleRate', 'Unknown'))
        channels = self.metadata.get('AudioChannels', self.metadata.get('Channels', 'Unknown'))
        
        if duration != 'Unknown':
            audio_info.append(f"Duration: {duration}")
        if bitrate != 'Unknown':
            audio_info.append(f"Bitrate: {bitrate}")
        if sample_rate != 'Unknown':
            audio_info.append(f"Sample Rate: {sample_rate}")
        if channels != 'Unknown':
            audio_info.append(f"Channels: {channels}")
        
        # Display audio info
        for info in audio_info:
            info_label = tk.Label(preview_container, text=info,
                                 font=("SF Pro Display", 12),
                                 bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
            info_label.pack(pady=2)
        
        # Album art if available
        self.try_load_album_art()
    
    def try_load_album_art(self):
        """Try to extract and display album art"""
        try:
            # Try to extract album art using exiftool
            cmd = [self.exiftool_path, '-Picture', '-b', self.current_file]
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0 and result.stdout:
                # Create image from binary data
                from io import BytesIO
                image = Image.open(BytesIO(result.stdout))
                image.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                
                # Add some spacing
                tk.Frame(self.preview_frame, height=20, bg=COLORS['bg_tertiary']).pack()
                
                # Display album art
                art_label = tk.Label(self.preview_frame, image=photo,
                                    bg=COLORS['bg_tertiary'])
                art_label.image = photo
                art_label.pack()
        except:
            pass  # No album art available
    
    def load_video_preview(self):
        """Load video file preview"""
        preview_container = tk.Frame(self.preview_frame, bg=COLORS['bg_tertiary'])
        preview_container.pack(expand=True)
        
        # Large video icon
        icon_label = tk.Label(preview_container, text="🎬", font=("SF Pro Display", 72),
                             bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'])
        icon_label.pack(pady=(0, 20))
        
        # Get video metadata
        video_info = []
        
        # Extract relevant video metadata
        duration = self.metadata.get('Duration', 'Unknown')
        dimensions = f"{self.metadata.get('ImageWidth', '?')}×{self.metadata.get('ImageHeight', '?')}"
        frame_rate = self.metadata.get('VideoFrameRate', self.metadata.get('FrameRate', 'Unknown'))
        codec = self.metadata.get('CompressorID', self.metadata.get('VideoCodec', 'Unknown'))
        
        if duration != 'Unknown':
            video_info.append(f"Duration: {duration}")
        video_info.append(f"Dimensions: {dimensions}")
        if frame_rate != 'Unknown':
            video_info.append(f"Frame Rate: {frame_rate}")
        if codec != 'Unknown':
            video_info.append(f"Codec: {codec}")
        
        # Display video info
        for info in video_info:
            info_label = tk.Label(preview_container, text=info,
                                 font=("SF Pro Display", 12),
                                 bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
            info_label.pack(pady=2)
    
    def load_document_preview(self):
        """Load document preview"""
        preview_container = tk.Frame(self.preview_frame, bg=COLORS['bg_tertiary'])
        preview_container.pack(expand=True)
        
        # Document icon
        icon_label = tk.Label(preview_container, text="📄", font=("SF Pro Display", 72),
                             bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'])
        icon_label.pack(pady=(0, 20))
        
        # Document info
        doc_info = []
        
        # Extract relevant document metadata
        title = self.metadata.get('Title', '')
        author = self.metadata.get('Author', self.metadata.get('Creator', ''))
        pages = self.metadata.get('PageCount', self.metadata.get('Pages', ''))
        
        if title:
            doc_info.append(f"Title: {title}")
        if author:
            doc_info.append(f"Author: {author}")
        if pages:
            doc_info.append(f"Pages: {pages}")
        
        # Display document info
        for info in doc_info:
            info_label = tk.Label(preview_container, text=info,
                                 font=("SF Pro Display", 12),
                                 bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
            info_label.pack(pady=2)
    
    def load_generic_preview(self):
        """Load generic file preview"""
        preview_container = tk.Frame(self.preview_frame, bg=COLORS['bg_tertiary'])
        preview_container.pack(expand=True)
        
        # File icon
        icon_label = tk.Label(preview_container, text="📎", font=("SF Pro Display", 72),
                             bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'])
        icon_label.pack(pady=(0, 20))
        
        # File info
        file_path = Path(self.current_file)
        mime_type = mimetypes.guess_type(self.current_file)[0] or "Unknown"
        
        info_label = tk.Label(preview_container, text=f"MIME Type: {mime_type}",
                             font=("SF Pro Display", 12),
                             bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
        info_label.pack(pady=2)
    
    def show_preview_error(self, error_msg):
        """Show preview error message"""
        error_label = tk.Label(self.preview_frame, 
                              text=f"Preview unavailable\n{error_msg}",
                              font=("SF Pro Display", 12),
                              bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'],
                              justify=tk.CENTER)
        error_label.pack(expand=True)
    
    def edit_tag(self, event):
        """Edit a tag value with modern dialog"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.tree.parent(item)
        
        # Don't edit categories
        if not parent:
            return
        
        # Get current values
        tag_name = self.tree.item(item, 'text')
        current_value = self.tree.item(item, 'values')[0]
        category = self.tree.item(parent, 'text').split(' ', 1)[1]  # Remove icon
        
        # Create modern edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {tag_name}")
        dialog.geometry("500x250")
        dialog.configure(bg=COLORS['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content frame
        content = tk.Frame(dialog, bg=COLORS['bg_primary'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Tag info
        tag_frame = tk.Frame(content, bg=COLORS['bg_secondary'])
        tag_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(tag_frame, text=f"{category}:{tag_name}", 
                font=("SF Pro Display", 14, "bold"),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Current value (if not too long)
        if len(str(current_value)) < 50:
            current_frame = tk.Frame(content, bg=COLORS['bg_primary'])
            current_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(current_frame, text="Current:", 
                    font=("SF Pro Display", 11),
                    bg=COLORS['bg_primary'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
            
            tk.Label(current_frame, text=str(current_value), 
                    font=("SF Pro Display", 11),
                    bg=COLORS['bg_primary'], fg=COLORS['text_primary']).pack(side=tk.LEFT, padx=(10, 0))
        
        # New value input
        input_frame = tk.Frame(content, bg=COLORS['bg_primary'])
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(input_frame, text="New value:", 
                font=("SF Pro Display", 11),
                bg=COLORS['bg_primary'], fg=COLORS['text_secondary']).pack(anchor=tk.W, pady=(0, 5))
        
        # Check if we need multiline input
        if len(str(current_value)) > 50 or '\n' in str(current_value):
            # Multi-line input
            text_frame = tk.Frame(input_frame, bg=COLORS['bg_tertiary'], highlightbackground=COLORS['border'], highlightthickness=1)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            value_text = tk.Text(text_frame, height=4, wrap=tk.WORD,
                                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                insertbackground=COLORS['text_primary'],
                                font=("SF Pro Display", 11), relief=tk.FLAT)
            value_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            value_text.insert('1.0', str(current_value))
            
            get_value = lambda: value_text.get('1.0', 'end-1c')
        else:
            # Single line input
            value_var = tk.StringVar(value=str(current_value))
            value_entry = ModernEntry(input_frame, textvariable=value_var)
            value_entry.pack(fill=tk.X)
            
            get_value = lambda: value_var.get()
        
        # Buttons
        button_frame = tk.Frame(content, bg=COLORS['bg_primary'])
        button_frame.pack(side=tk.BOTTOM)
        
        def save_edit():
            new_value = get_value()
            full_tag = f"{category}:{tag_name}" if category != 'File' else tag_name
            self.metadata[full_tag] = new_value
            self.modified_fields.add(full_tag)
            self.tree.item(item, values=(new_value if len(new_value) <= 100 else new_value[:97] + "...",), 
                          tags=('modified',))
            dialog.destroy()
            self.status_var.set(f"Modified: {full_tag}")
        
        ModernButton(button_frame, text="Cancel", command=dialog.destroy, 
                    style="secondary").pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(button_frame, text="Save", command=save_edit, 
                    style="primary").pack(side=tk.LEFT)
        
        # Focus on input
        if 'value_entry' in locals():
            value_entry.focus()
            value_entry.select_range(0, tk.END)
        else:
            value_text.focus()
    
    def save_changes(self):
        """Save modified metadata back to file"""
        if not self.current_file or not self.modified_fields:
            messagebox.showinfo("Info", "No changes to save")
            return
        
        try:
            # Build exiftool command
            cmd = [self.exiftool_path, '-overwrite_original']
            
            # Add each modified field
            for field in self.modified_fields:
                value = self.metadata.get(field, '')
                # Handle special characters in values
                if isinstance(value, str):
                    value = value.replace('"', '\\"')
                cmd.append(f'-{field}={value}')
            
            cmd.append(self.current_file)
            
            # Run exiftool
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "Changes saved successfully")
                self.modified_fields.clear()
                self.load_metadata()  # Reload to confirm changes
                self.status_var.set("Changes saved")
            else:
                messagebox.showerror("Error", f"Failed to save changes: {result.stderr}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
    
    def export_metadata(self):
        """Export metadata as JSON"""
        if not self.metadata:
            messagebox.showinfo("Info", "No metadata to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Metadata",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", "Metadata exported successfully")
                self.status_var.set(f"Exported to: {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def import_metadata(self):
        """Import metadata from JSON"""
        filename = filedialog.askopenfilename(
            title="Import Metadata",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                # Update metadata with imported values
                count = 0
                for key, value in imported_data.items():
                    if key in self.metadata:
                        self.metadata[key] = value
                        self.modified_fields.add(key)
                        count += 1
                
                self.display_metadata()
                messagebox.showinfo("Success", f"Imported {count} tags")
                self.status_var.set(f"Imported {count} tags from {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")
    
    def copy_all_tags(self):
        """Copy all metadata tags to clipboard"""
        if not self.metadata:
            return
        
        self.clipboard_data = self.metadata.copy()
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(self.metadata, indent=2, ensure_ascii=False))
        self.status_var.set(f"Copied {len(self.metadata)} tags to clipboard")
    
    def paste_tags(self):
        """Paste tags from clipboard"""
        if not self.clipboard_data:
            try:
                clipboard = self.root.clipboard_get()
                self.clipboard_data = json.loads(clipboard)
            except:
                messagebox.showerror("Error", "No valid metadata in clipboard")
                return
        
        count = 0
        for key, value in self.clipboard_data.items():
            if key in self.metadata:
                self.metadata[key] = value
                self.modified_fields.add(key)
                count += 1
        
        self.display_metadata()
        self.status_var.set(f"Pasted {count} tags")
    
    def remove_all_tags(self):
        """Remove all metadata tags"""
        if not self.current_file:
            return
        
        if messagebox.askyesno("Confirm", "Remove all metadata from this file?\n\nThis action cannot be undone."):
            try:
                cmd = [self.exiftool_path, '-all=', '-overwrite_original', self.current_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    messagebox.showinfo("Success", "All metadata removed")
                    self.load_metadata()
                    self.status_var.set("All metadata removed")
                else:
                    messagebox.showerror("Error", f"Failed to remove metadata: {result.stderr}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove metadata: {str(e)}")
    
    def show_modified_only(self):
        """Show only modified tags"""
        if not self.modified_fields:
            messagebox.showinfo("Info", "No modified tags")
            return
        
        # Clear and show only modified
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Group modified tags
        categories = defaultdict(list)
        for key in self.modified_fields:
            value = self.metadata.get(key, '')
            if ':' in key:
                category, tag = key.split(':', 1)
            else:
                category = 'File'
                tag = key
            categories[category].append((tag, value))
        
        # Display
        for category in sorted(categories.keys()):
            parent = self.tree.insert('', 'end', text=category, open=True, tags=('category',))
            for tag, value in sorted(categories[category]):
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:97] + "..."
                self.tree.insert(parent, 'end', text=tag, values=(display_value,), tags=('modified',))
    
    def expand_all(self):
        """Expand all tree items"""
        for item in self.tree.get_children():
            self.tree.item(item, open=True)
    
    def collapse_all(self):
        """Collapse all tree items"""
        for item in self.tree.get_children():
            self.tree.item(item, open=False)
    
    def batch_process(self):
        """Open batch processing dialog"""
        BatchProcessDialog(self.root, self.exiftool_path)
    
    def datetime_shift(self):
        """Open date/time shift dialog"""
        if not self.current_file:
            messagebox.showinfo("Info", "Please open a file first")
            return
        
        DateTimeShiftDialog(self.root, self.current_file, self.exiftool_path, self.load_metadata)
    
    def template_manager(self):
        """Open template manager dialog"""
        TemplateManagerDialog(self.root, self.exiftool_path)


class BatchProcessDialog:
    def __init__(self, parent, exiftool_path):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Batch Process")
        self.dialog.geometry("700x500")
        self.dialog.configure(bg=COLORS['bg_primary'])
        self.exiftool_path = exiftool_path
        self.files = []
        
        # Main container
        main_frame = tk.Frame(self.dialog, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_frame, text="Batch Process Files", 
                font=("SF Pro Display", 18, "bold"),
                bg=COLORS['bg_primary'], fg=COLORS['text_primary']).pack(pady=(0, 20))
        
        # File list section
        list_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # File list header
        header_frame = tk.Frame(list_frame, bg=COLORS['bg_secondary'])
        header_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(header_frame, text="Files to process:", 
                font=("SF Pro Display", 12, "bold"),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(side=tk.LEFT)
        
        self.count_label = tk.Label(header_frame, text="0 files", 
                                   font=("SF Pro Display", 11),
                                   bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'])
        self.count_label.pack(side=tk.RIGHT)
        
        # File listbox
        listbox_frame = tk.Frame(list_frame, bg=COLORS['bg_tertiary'])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.file_listbox = tk.Listbox(listbox_frame, height=10,
                                      bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                      selectbackground=COLORS['accent'],
                                      selectforeground=COLORS['text_primary'],
                                      font=("SF Pro Display", 11),
                                      relief=tk.FLAT)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ModernButton(button_frame, text="Add Files", command=self.add_files, 
                    style="secondary").pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(button_frame, text="Add Folder", command=self.add_folder, 
                    style="secondary").pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(button_frame, text="Clear", command=self.clear_files, 
                    style="secondary").pack(side=tk.LEFT)
        
        # Operations
        tk.Label(main_frame, text="Operation:", 
                font=("SF Pro Display", 12, "bold"),
                bg=COLORS['bg_primary'], fg=COLORS['text_primary']).pack(anchor=tk.W, pady=(20, 10))
        
        self.operation_var = tk.StringVar(value="remove_all")
        
        operations = [
            ("Remove all metadata", "remove_all"),
            ("Copy metadata from template", "copy_template"),
            ("Apply specific tags", "apply_tags"),
            ("Shift date/time", "shift_datetime")
        ]
        
        for text, value in operations:
            rb = tk.Radiobutton(main_frame, text=text, variable=self.operation_var, value=value,
                               font=("SF Pro Display", 11),
                               bg=COLORS['bg_primary'], fg=COLORS['text_primary'],
                               selectcolor=COLORS['bg_primary'],
                               activebackground=COLORS['bg_primary'],
                               activeforeground=COLORS['text_primary'])
            rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Process button
        process_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        process_frame.pack(fill=tk.X, pady=(30, 0))
        
        ModernButton(process_frame, text="Process Files", command=self.process_files, 
                    style="primary").pack(side=tk.RIGHT)
    
    def add_files(self):
        """Add files to process"""
        files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("All files", "*.*")]
        )
        
        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)
        
        self.update_count()
    
    def add_folder(self):
        """Add all files from a folder"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            # Get all files with supported extensions
            all_extensions = []
            for info in FILE_CATEGORIES.values():
                all_extensions.extend(info['extensions'])
                all_extensions.extend(info.get('raw_formats', []))
            
            for file_path in Path(folder).iterdir():
                if file_path.is_file() and file_path.suffix.lower() in all_extensions:
                    if str(file_path) not in self.files:
                        self.files.append(str(file_path))
                        self.file_listbox.insert(tk.END, file_path.name)
            
            self.update_count()
    
    def clear_files(self):
        """Clear file list"""
        self.files = []
        self.file_listbox.delete(0, tk.END)
        self.update_count()
    
    def update_count(self):
        """Update file count label"""
        count = len(self.files)
        self.count_label.config(text=f"{count} file{'s' if count != 1 else ''}")
    
    def process_files(self):
        """Process all files"""
        if not self.files:
            messagebox.showinfo("Info", "No files to process")
            return
        
        operation = self.operation_var.get()
        
        if operation == "remove_all":
            if messagebox.askyesno("Confirm", f"Remove all metadata from {len(self.files)} files?"):
                progress = ProgressDialog(self.dialog, "Processing files...", len(self.files))
                
                for i, file in enumerate(self.files):
                    progress.update(i, f"Processing: {Path(file).name}")
                    cmd = [self.exiftool_path, '-all=', '-overwrite_original', file]
                    subprocess.run(cmd, capture_output=True)
                
                progress.close()
                messagebox.showinfo("Success", f"Processed {len(self.files)} files")
                self.dialog.destroy()


class DateTimeShiftDialog:
    def __init__(self, parent, current_file, exiftool_path, callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Date/Time Shift")
        self.dialog.geometry("450x400")
        self.dialog.configure(bg=COLORS['bg_primary'])
        self.current_file = current_file
        self.exiftool_path = exiftool_path
        self.callback = callback
        
        # Main container
        main_frame = tk.Frame(self.dialog, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_frame, text="Shift Date/Time", 
                font=("SF Pro Display", 18, "bold"),
                bg=COLORS['bg_primary'], fg=COLORS['text_primary']).pack(pady=(0, 10))
        
        tk.Label(main_frame, text="Adjust all date/time tags by:", 
                font=("SF Pro Display", 12),
                bg=COLORS['bg_primary'], fg=COLORS['text_secondary']).pack(pady=(0, 20))
        
        # Input fields
        fields_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'])
        fields_frame.pack(fill=tk.X, pady=10)
        
        # Create spinbox fields
        self.fields = {}
        units = [
            ("Years", "years", -10, 10),
            ("Months", "months", -12, 12),
            ("Days", "days", -365, 365),
            ("Hours", "hours", -24, 24),
            ("Minutes", "minutes", -60, 60)
        ]
        
        for label, key, from_val, to_val in units:
            row_frame = tk.Frame(fields_frame, bg=COLORS['bg_secondary'])
            row_frame.pack(fill=tk.X, padx=15, pady=5)
            
            tk.Label(row_frame, text=f"{label}:", width=10, anchor=tk.E,
                    font=("SF Pro Display", 11),
                    bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(side=tk.LEFT, padx=(0, 10))
            
            var = tk.StringVar(value="0")
            self.fields[key] = var
            
            spinbox = tk.Spinbox(row_frame, from_=from_val, to=to_val, textvariable=var,
                                width=10, font=("SF Pro Display", 11),
                                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                buttonbackground=COLORS['bg_tertiary'],
                                relief=tk.FLAT)
            spinbox.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        button_frame.pack(side=tk.BOTTOM, pady=(20, 0))
        
        ModernButton(button_frame, text="Cancel", command=self.dialog.destroy, 
                    style="secondary").pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(button_frame, text="Apply", command=self.apply_shift, 
                    style="primary").pack(side=tk.LEFT)
    
    def apply_shift(self):
        """Apply the date/time shift"""
        # Get values
        years = int(self.fields['years'].get())
        months = int(self.fields['months'].get())
        days = int(self.fields['days'].get())
        hours = int(self.fields['hours'].get())
        minutes = int(self.fields['minutes'].get())
        
        # Build shift string
        shift_parts = []
        if years: shift_parts.append(f"{years:+d}:0:0")
        if months: shift_parts.append(f"0:{months:+d}:0")
        if days: shift_parts.append(f"0:0:{days:+d}")
        if hours or minutes: shift_parts.append(f"{hours:+d}:{minutes:+02d}:0")
        
        if not shift_parts:
            messagebox.showinfo("Info", "No shift specified")
            return
        
        shift_string = " ".join(shift_parts)
        
        try:
            cmd = [self.exiftool_path, '-overwrite_original', f'-AllDates+={shift_string}', self.current_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "Date/time shifted successfully")
                self.callback()  # Reload metadata
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", f"Failed to shift date/time: {result.stderr}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to shift date/time: {str(e)}")


class TemplateManagerDialog:
    def __init__(self, parent, exiftool_path):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Template Manager")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg=COLORS['bg_primary'])
        self.exiftool_path = exiftool_path
        self.templates = self.load_templates()
        
        # Main container
        main_frame = tk.Frame(self.dialog, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_frame, text="Metadata Templates", 
                font=("SF Pro Display", 18, "bold"),
                bg=COLORS['bg_primary'], fg=COLORS['text_primary']).pack(pady=(0, 20))
        
        # Template list
        list_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'])
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(list_frame, text="Templates", 
                font=("SF Pro Display", 14, "bold"),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(padx=15, pady=10)
        
        # Template listbox
        listbox_frame = tk.Frame(list_frame, bg=COLORS['bg_tertiary'])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.template_listbox = tk.Listbox(listbox_frame,
                                          bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                          selectbackground=COLORS['accent'],
                                          selectforeground=COLORS['text_primary'],
                                          font=("SF Pro Display", 11),
                                          relief=tk.FLAT)
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.template_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Template buttons
        template_buttons = tk.Frame(list_frame, bg=COLORS['bg_secondary'])
        template_buttons.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ModernButton(template_buttons, text="New", command=self.new_template, 
                    style="secondary").pack(side=tk.LEFT, padx=(0, 5))
        ModernButton(template_buttons, text="Delete", command=self.delete_template, 
                    style="secondary").pack(side=tk.LEFT)
        
        # Template details
        details_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'])
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(details_frame, text="Template Details", 
                font=("SF Pro Display", 14, "bold"),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(padx=15, pady=10)
        
        # Template name
        name_frame = tk.Frame(details_frame, bg=COLORS['bg_secondary'])
        name_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(name_frame, text="Name:", 
                font=("SF Pro Display", 11),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.name_var = tk.StringVar()
        self.name_entry = ModernEntry(name_frame, textvariable=self.name_var)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Template tags
        tk.Label(details_frame, text="Tags:", 
                font=("SF Pro Display", 11),
                bg=COLORS['bg_secondary'], fg=COLORS['text_primary']).pack(anchor=tk.W, padx=15, pady=(10, 5))
        
        # Tags text area
        text_frame = tk.Frame(details_frame, bg=COLORS['bg_tertiary'], 
                             highlightbackground=COLORS['border'], highlightthickness=1)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.tags_text = tk.Text(text_frame, wrap=tk.WORD,
                                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                insertbackground=COLORS['text_primary'],
                                font=("SF Pro Display", 11), relief=tk.FLAT)
        self.tags_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Save button
        ModernButton(details_frame, text="Save Template", command=self.save_template, 
                    style="primary").pack(pady=(0, 15))
        
        # Load existing templates
        self.refresh_template_list()
    
    def load_templates(self):
        """Load templates from file"""
        template_file = Path.home() / '.exiftool_gui_templates.json'
        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_templates(self):
        """Save templates to file"""
        template_file = Path.home() / '.exiftool_gui_templates.json'
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)
    
    def refresh_template_list(self):
        """Refresh template list"""
        self.template_listbox.delete(0, tk.END)
        for name in sorted(self.templates.keys()):
            self.template_listbox.insert(tk.END, name)
    
    def on_template_select(self, event):
        """Handle template selection"""
        selection = self.template_listbox.curselection()
        if selection:
            name = self.template_listbox.get(selection[0])
            self.name_var.set(name)
            
            # Display template content
            template = self.templates[name]
            self.tags_text.delete('1.0', tk.END)
            
            for key, value in template.items():
                self.tags_text.insert(tk.END, f"{key}={value}\n")
    
    def new_template(self):
        """Create new template"""
        self.name_var.set("New Template")
        self.tags_text.delete('1.0', tk.END)
        self.tags_text.insert('1.0', "# Enter tags in format: TagName=Value\n")
        self.tags_text.insert(tk.END, "# Example:\n")
        self.tags_text.insert(tk.END, "# Artist=Your Name\n")
        self.tags_text.insert(tk.END, "# Copyright=© 2024 Your Name\n")
        self.name_entry.focus()
        self.name_entry.select_range(0, tk.END)
    
    def save_template(self):
        """Save current template"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a template name")
            return
        
        # Parse tags
        tags = {}
        content = self.tags_text.get('1.0', 'end-1c')
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                tags[key.strip()] = value.strip()
        
        if not tags:
            messagebox.showerror("Error", "No valid tags found")
            return
        
        self.templates[name] = tags
        self.save_templates()
        self.refresh_template_list()
        messagebox.showinfo("Success", f"Template '{name}' saved")
    
    def delete_template(self):
        """Delete selected template"""
        selection = self.template_listbox.curselection()
        if selection:
            name = self.template_listbox.get(selection[0])
            if messagebox.askyesno("Confirm", f"Delete template '{name}'?"):
                del self.templates[name]
                self.save_templates()
                self.refresh_template_list()
                self.name_var.set("")
                self.tags_text.delete('1.0', tk.END)


class ProgressDialog:
    def __init__(self, parent, title, total):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.configure(bg=COLORS['bg_primary'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Content
        main_frame = tk.Frame(self.dialog, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.label = tk.Label(main_frame, text="Processing...", 
                             font=("SF Pro Display", 12),
                             bg=COLORS['bg_primary'], fg=COLORS['text_primary'])
        self.label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, 
                                           variable=self.progress_var,
                                           maximum=total,
                                           length=350)
        self.progress_bar.pack(pady=10)
        
        self.status_label = tk.Label(main_frame, text="", 
                                    font=("SF Pro Display", 10),
                                    bg=COLORS['bg_primary'], fg=COLORS['text_secondary'])
        self.status_label.pack()
        
        self.dialog.update()
    
    def update(self, current, message=""):
        """Update progress"""
        self.progress_var.set(current)
        if message:
            self.status_label.config(text=message)
        self.dialog.update()
    
    def close(self):
        """Close dialog"""
        self.dialog.destroy()


def main():
    root = tk.Tk()
    
    # Set app icon if available
    try:
        if platform.system() == 'Darwin':
            # macOS specific icon setting
            root.iconbitmap('icon.icns')
    except:
        pass
    
    app = ExifToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()