#!/bin/bash

# ExifTool GUI Build Script
# This script builds the macOS application and creates a DMG installer

set -e

echo "ExifTool GUI Build Script"
echo "========================"

# Configuration
APP_NAME="ExifTool GUI"
VERSION="1.0.0"
BUNDLE_ID="com.yourcompany.exiftoolgui"
DMG_NAME="ExifToolGUI-${VERSION}.dmg"
BUILD_DIR="build"
DIST_DIR="dist"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for required tools
check_requirements() {
    echo "Checking requirements..."
    
    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        exit 1
    fi
    
    # Check for exiftool
    if ! command -v exiftool &> /dev/null; then
        echo -e "${YELLOW}Warning: ExifTool is not installed${NC}"
        echo "Users will need to install it separately using:"
        echo "  brew install exiftool"
        echo ""
    fi
    
    # Check for create-dmg (optional, for DMG creation)
    if ! command -v create-dmg &> /dev/null; then
        echo -e "${YELLOW}Warning: create-dmg is not installed${NC}"
        echo "Install it using: brew install create-dmg"
        echo "Skipping DMG creation..."
        NO_DMG=1
    fi
    
    echo -e "${GREEN}Requirements check passed${NC}"
}

# Create virtual environment and install dependencies
setup_environment() {
    echo "Setting up build environment..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install py2app Pillow
    
    echo -e "${GREEN}Environment setup complete${NC}"
}

# Create app icon (placeholder if icon.icns doesn't exist)
create_icon() {
    if [ ! -f "icon.icns" ]; then
        echo "Creating app icon..."
        
        # Check if we have the icon generator script
        if [ -f "generate_icon.py" ]; then
            python generate_icon.py
        else
            echo "Creating placeholder icon..."
            # Create a simple icon using iconutil
            mkdir -p icon.iconset
            
            # Create a simple colored square as placeholder
            for size in 16 32 64 128 256 512 1024; do
                convert -size ${size}x${size} xc:'#2040A0' \
                    -fill white -gravity center -pointsize $((size/3)) \
                    -annotate +0+0 'EXIF' \
                    icon.iconset/icon_${size}x${size}.png 2>/dev/null || {
                    # If ImageMagick not available, create with sips
                    echo "Warning: Could not create icon size ${size}x${size}"
                }
            done
            
            # Create @2x versions
            cp icon.iconset/icon_32x32.png icon.iconset/icon_16x16@2x.png 2>/dev/null
            cp icon.iconset/icon_64x64.png icon.iconset/icon_32x32@2x.png 2>/dev/null
            cp icon.iconset/icon_256x256.png icon.iconset/icon_128x128@2x.png 2>/dev/null
            cp icon.iconset/icon_512x512.png icon.iconset/icon_256x256@2x.png 2>/dev/null
            cp icon.iconset/icon_1024x1024.png icon.iconset/icon_512x512@2x.png 2>/dev/null
            
            # Convert to icns
            iconutil -c icns icon.iconset -o icon.icns 2>/dev/null || {
                echo -e "${YELLOW}Warning: Could not create icon file${NC}"
                touch icon.icns  # Create empty file to prevent build error
            }
            
            # Cleanup
            rm -rf icon.iconset
        fi
    fi
}

# Build the application
build_app() {
    echo "Building application..."
    
    # Clean previous builds
    rm -rf "$BUILD_DIR" "$DIST_DIR"
    
    # Run py2app
    python setup.py py2app
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Build successful${NC}"
    else
        echo -e "${RED}Build failed${NC}"
        exit 1
    fi
}

# Code sign the application (optional, requires developer certificate)
sign_app() {
    if [ -n "$DEVELOPER_ID" ]; then
        echo "Code signing application..."
        codesign --deep --force --verify --verbose --sign "$DEVELOPER_ID" \
            --options runtime \
            --entitlements entitlements.plist \
            "dist/${APP_NAME}.app"
        
        echo -e "${GREEN}Code signing complete${NC}"
    else
        echo -e "${YELLOW}Skipping code signing (no DEVELOPER_ID set)${NC}"
    fi
}

# Create DMG installer
create_dmg_installer() {
    if [ -n "$NO_DMG" ]; then
        return
    fi
    
    echo "Creating DMG installer..."
    
    # Create temporary directory for DMG contents
    DMG_TEMP="dmg-temp"
    rm -rf "$DMG_TEMP"
    mkdir -p "$DMG_TEMP"
    
    # Copy app to DMG directory
    cp -R "dist/${APP_NAME}.app" "$DMG_TEMP/"
    
    # Create README
    cat > "$DMG_TEMP/README.txt" << EOF
ExifTool GUI v${VERSION}
====================

Installation:
1. Drag the ExifTool GUI app to your Applications folder
2. Install ExifTool if not already installed:
   brew install exiftool

Usage:
- Double-click to launch the application
- Use File > Open to select an image
- Double-click any EXIF tag to edit its value
- Save changes with File > Save or Cmd+S

Requirements:
- macOS 10.15 or later
- ExifTool command line tool

Support:
Visit https://github.com/yourusername/exiftool-gui

EOF
    
    # Create DMG
    create-dmg \
        --volname "$APP_NAME" \
        --volicon "icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 150 150 \
        --icon "README.txt" 450 150 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 300 250 \
        --no-internet-enable \
        "$DMG_NAME" \
        "$DMG_TEMP"
    
    # Cleanup
    rm -rf "$DMG_TEMP"
    
    echo -e "${GREEN}DMG created: $DMG_NAME${NC}"
}

# Create a simple installer package (alternative to DMG)
create_pkg_installer() {
    echo "Creating PKG installer..."
    
    # Create package structure
    PKG_ROOT="pkg-root"
    rm -rf "$PKG_ROOT"
    mkdir -p "$PKG_ROOT/Applications"
    
    # Copy app
    cp -R "dist/${APP_NAME}.app" "$PKG_ROOT/Applications/"
    
    # Create component plist
    cat > component.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<array>
    <dict>
        <key>BundleHasStrictIdentifier</key>
        <true/>
        <key>BundleIsRelocatable</key>
        <true/>
        <key>BundleIsVersionChecked</key>
        <true/>
        <key>BundleOverwriteAction</key>
        <string>upgrade</string>
        <key>RootRelativeBundlePath</key>
        <string>Applications/${APP_NAME}.app</string>
    </dict>
</array>
</plist>
EOF
    
    # Build package
    pkgbuild \
        --root "$PKG_ROOT" \
        --component-plist component.plist \
        --identifier "$BUNDLE_ID" \
        --version "$VERSION" \
        --install-location "/" \
        "ExifToolGUI-${VERSION}.pkg"
    
    # Cleanup
    rm -rf "$PKG_ROOT" component.plist
    
    echo -e "${GREEN}PKG created: ExifToolGUI-${VERSION}.pkg${NC}"
}

# Create release archive for GitHub
create_release_archive() {
    echo "Creating release archive..."
    
    RELEASE_DIR="ExifToolGUI-${VERSION}"
    rm -rf "$RELEASE_DIR" "${RELEASE_DIR}.zip"
    mkdir -p "$RELEASE_DIR"
    
    # Copy application
    cp -R "dist/${APP_NAME}.app" "$RELEASE_DIR/"
    
    # Create installation instructions
    cat > "$RELEASE_DIR/INSTALL.txt" << EOF
ExifTool GUI Installation Instructions
=====================================

1. Install ExifTool (if not already installed):
   - Using Homebrew: brew install exiftool
   - Or download from: https://exiftool.org

2. Install ExifTool GUI:
   - Drag "ExifTool GUI.app" to your Applications folder
   - Right-click and select "Open" the first time (macOS security)

3. Launch and enjoy!

Troubleshooting:
- If the app doesn't open, check System Preferences > Security & Privacy
- Make sure ExifTool is installed and in your PATH

EOF
    
    # Create README for GitHub
    cat > README.md << 'EOF'
# ExifTool GUI

A native macOS application for viewing and editing EXIF metadata using Phil Harvey's ExifTool.

![ExifTool GUI Screenshot](screenshot.png)

## Features

- **Visual Interface**: User-friendly GUI for ExifTool
- **Live Preview**: See image thumbnails while editing
- **Batch Processing**: Process multiple files at once
- **Search & Filter**: Quickly find specific EXIF tags
- **Import/Export**: Save and load EXIF data as JSON
- **Date/Time Shift**: Easily adjust timestamps on photos
- **Native macOS**: Built specifically for macOS with native look and feel

## Requirements

- macOS 10.15 (Catalina) or later
- [ExifTool](https://exiftool.org) by Phil Harvey

## Installation

### Option 1: Download Release

1. Download the latest release from the [Releases](https://github.com/yourusername/exiftool-gui/releases) page
2. Open the DMG file and drag ExifTool GUI to your Applications folder
3. Install ExifTool if not already installed:
   ```bash
   brew install exiftool
   ```

### Option 2: Build from Source

1. Clone this repository
2. Run the build script:
   ```bash
   ./build.sh
   ```
3. Find the built application in the `dist` folder

## Usage

1. Launch ExifTool GUI
2. Use **File > Open** or drag an image file to the window
3. Browse and search EXIF tags in the right panel
4. Double-click any tag to edit its value
5. Save changes with **File > Save** or **Cmd+S**

### Keyboard Shortcuts

- `Cmd+O` - Open file
- `Cmd+S` - Save changes
- `Cmd+Q` - Quit

## Building from Source

### Prerequisites

- Python 3.8 or later
- pip
- ExifTool

### Build Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/exiftool-gui.git
cd exiftool-gui

# Run the build script
chmod +x build.sh
./build.sh

# The app will be in dist/ExifTool GUI.app
```

## Development

The application is built with:
- Python 3
- Tkinter (included with Python)
- Pillow for image handling
- py2app for macOS packaging

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Phil Harvey](https://exiftool.org) for creating the amazing ExifTool
- All contributors and testers

## Support

If you encounter any issues or have suggestions, please [open an issue](https://github.com/yourusername/exiftool-gui/issues).
EOF
    
    # Create LICENSE file
    cat > LICENSE << EOF
MIT License

Copyright (c) $(date +%Y) Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    
    # Create ZIP archive
    zip -r "${RELEASE_DIR}.zip" "$RELEASE_DIR"
    
    # Cleanup
    rm -rf "$RELEASE_DIR"
    
    echo -e "${GREEN}Release archive created: ${RELEASE_DIR}.zip${NC}"
}

# Main build process
main() {
    echo "Starting build process..."
    echo ""
    
    check_requirements
    setup_environment
    create_icon
    build_app
    sign_app
    
    # Create installers
    create_dmg_installer
    create_pkg_installer
    create_release_archive
    
    # Summary
    echo ""
    echo "Build Summary"
    echo "============="
    echo -e "${GREEN}✓ Application built successfully${NC}"
    echo "  Location: dist/${APP_NAME}.app"
    
    if [ ! -n "$NO_DMG" ]; then
        echo -e "${GREEN}✓ DMG installer created${NC}"
        echo "  Location: $DMG_NAME"
    fi
    
    echo -e "${GREEN}✓ PKG installer created${NC}"
    echo "  Location: ExifToolGUI-${VERSION}.pkg"
    
    echo -e "${GREEN}✓ Release archive created${NC}"
    echo "  Location: ExifToolGUI-${VERSION}.zip"
    
    echo ""
    echo "Next steps:"
    echo "1. Test the application thoroughly"
    echo "2. Upload release files to GitHub"
    echo "3. Create release notes"
    
    # Deactivate virtual environment
    deactivate
}

# Run main function
main