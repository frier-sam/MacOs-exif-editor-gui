"""
Setup script for ExifTool GUI
Builds a macOS application bundle
"""

from setuptools import setup
import sys
import os


# Application metadata
APP = ['exiftool_gui.py']
APP_NAME = 'ExifTool GUI'
VERSION = '1.0.0'

DATA_FILES = []

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': 'com.yourcompany.exiftoolgui',
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'NSRequiresAquaSystemAppearance': False,
        'LSArchitecturePriority': ['arm64', 'x86_64'],  # Support Apple Silicon
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Image Files',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'heic', 'heif', 'raw', 'cr2', 'cr3', 'nef', 'arw', 'dng', 'orf', 'rw2', 'raf', 'srw'],
                'LSHandlerRank': 'Default'
            },
            {
                'CFBundleTypeName': 'Audio Files',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 'aiff', 'ape'],
                'LSHandlerRank': 'Default'
            },
            {
                'CFBundleTypeName': 'Video Files',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg'],
                'LSHandlerRank': 'Default'
            },
            {
                'CFBundleTypeName': 'Document Files',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'],
                'LSHandlerRank': 'Default'
            }
        ]
    },
    'packages': ['tkinter', 'PIL'],
    'includes': ['json', 'subprocess', 'threading', 'pathlib', 'mimetypes', 'collections'],
    'excludes': ['matplotlib', 'numpy', 'scipy'],
    'resources': [],
    'optimize': 2,
    'arch': 'universal2'  # Build for both Intel and Apple Silicon
}

setup(
    app=APP,
    name=APP_NAME,
    version=VERSION,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'Pillow>=9.0.0'
    ]
)
