# ExifTool GUI

A modern, native macOS application for viewing and editing metadata in images, audio, video, and document files using Phil Harvey's ExifTool.

![ExifTool GUI Screenshot](screenshot.png)

## Features

### 🎨 Modern Dark Interface
- Native macOS dark mode support
- Smooth animations and transitions
- Clean, professional design
- Responsive layout with resizable panels

### 📁 Universal File Support
- **Images**: JPEG, PNG, TIFF, RAW formats (CR2, NEF, ARW, etc.), HEIC/HEIF
- **Audio**: MP3, FLAC, WAV, AAC, OGG, M4A, and more
- **Video**: MP4, MOV, AVI, MKV, WebM, and more
- **Documents**: PDF, Word, Excel, PowerPoint
- **Archives**: ZIP, RAR, 7Z (metadata only)

### 🔍 Smart Features
- **Live Preview**: See images, audio waveforms, video info, and document details
- **Smart Search**: Quickly find specific metadata tags
- **Batch Processing**: Process multiple files at once
- **Template Manager**: Save and apply metadata templates
- **Date/Time Shift**: Easily adjust timestamps on photos
- **Modified Tags Highlighting**: See what you've changed at a glance

### 🛠️ Professional Tools
- **Import/Export**: Save metadata as JSON for backup or transfer
- **Copy/Paste Tags**: Quickly duplicate metadata between files
- **Keyboard Shortcuts**: Fast workflow with standard macOS shortcuts
- **Drag & Drop**: Natural file handling

## Requirements

- macOS 10.15 (Catalina) or later
- [ExifTool](https://exiftool.org) by Phil Harvey

## Installation

### Option 1: Download Release (Recommended)

1. Download the latest release from the [Releases](https://github.com/yourusername/exiftool-gui/releases) page
2. Open the DMG file and drag ExifTool GUI to your Applications folder
3. Install ExifTool if not already installed:
   ```bash
   brew install exiftool
   ```
4. Right-click the app and select "Open" the first time (macOS security)

### Option 2: Install via Package

1. Download the .pkg installer from the [Releases](https://github.com/yourusername/exiftool-gui/releases) page
2. Double-click to install
3. Install ExifTool:
   ```bash
   brew install exiftool
   ```

### Option 3: Build from Source

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/exiftool-gui.git
   cd exiftool-gui
   ```

2. Run the build script:
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

3. Find the built application in the `dist` folder

## Usage

### Basic Workflow

1. **Open a File**: Click "Open File" or use `Cmd+O`
2. **Browse Metadata**: Explore all metadata in the organized tree view
3. **Edit Tags**: Double-click any tag to edit its value
4. **Save Changes**: Click "Save Changes" or use `Cmd+S`

### Keyboard Shortcuts

- `Cmd+O` - Open file
- `Cmd+S` - Save changes
- `Cmd+F` - Focus search
- `Cmd+Q` - Quit application

### Advanced Features

#### Batch Processing
1. Go to **Tools > Batch Process**
2. Add files or folders
3. Select operation (remove all, apply template, etc.)
4. Click "Process Files"

#### Template Manager
1. Go to **Tools > Template Manager**
2. Create templates with commonly used metadata
3. Apply templates to single files or batches

#### Date/Time Shift
1. Open a file with date/time metadata
2. Go to **Tools > Date/Time Shift**
3. Specify the time adjustment
4. Apply to shift all date/time tags

## Building from Source

### Prerequisites

- Python 3.8 or later
- pip
- ExifTool
- Xcode Command Line Tools

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/exiftool-gui.git
cd exiftool-gui

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python exiftool_gui.py
```

### Building for Distribution

```bash
# Run the build script
./build.sh

# This will create:
# - ExifTool GUI.app (in dist/)
# - ExifToolGUI-1.0.0.dmg
# - ExifToolGUI-1.0.0.pkg
# - ExifToolGUI-1.0.0.zip
```

## Architecture

The application is built with:
- **Python 3** - Core application logic
- **Tkinter** - Native macOS UI framework
- **Pillow** - Image processing and preview
- **ExifTool** - Metadata reading and writing
- **py2app** - macOS application bundling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Guidelines

1. Follow PEP 8 style guidelines
2. Add comments for complex logic
3. Test with various file types
4. Update documentation as needed

## Troubleshooting

### App Won't Open
- Right-click and select "Open" to bypass Gatekeeper
- Check System Preferences > Security & Privacy
- Ensure ExifTool is installed: `which exiftool`

### ExifTool Not Found
```bash
# Install via Homebrew
brew install exiftool

# Or download from
# https://exiftool.org
```

### Preview Not Working
- Some file types may not support preview
- Check file permissions
- Ensure file is not corrupted

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Phil Harvey](https://exiftool.org) for creating the amazing ExifTool
- The Python community for excellent libraries
- All contributors and testers

## Changelog

### Version 1.0.0 (2025-05-27)
- Initial release
- Modern dark UI
- Support for images, audio, video, and documents
- Batch processing
- Template manager
- Date/time shifting

