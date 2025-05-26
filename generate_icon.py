#!/usr/bin/env python3
"""
Generate app icon for ExifTool GUI
Creates a modern icon with gradient and text
"""

from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
import sys

def create_icon_image(size):
    """Create an icon image at the specified size"""
    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background with gradient effect
    padding = size // 8
    corner_radius = size // 5
    
    # Create gradient background (dark blue to purple)
    for y in range(padding, size - padding):
        # Calculate gradient color
        progress = (y - padding) / (size - 2 * padding)
        r = int(20 + progress * 40)  # 20 to 60
        g = int(30 + progress * 20)  # 30 to 50
        b = int(80 + progress * 60)  # 80 to 140
        
        # Draw horizontal line
        draw.rectangle([(padding, y), (size - padding, y)], fill=(r, g, b, 255))
    
    # Create mask for rounded corners
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle on mask
    if hasattr(mask_draw, 'rounded_rectangle'):
        mask_draw.rounded_rectangle(
            [(padding, padding), (size - padding, size - padding)],
            radius=corner_radius,
            fill=255
        )
    else:
        # Fallback for older Pillow versions
        mask_draw.rectangle(
            [(padding, padding), (size - padding, size - padding)],
            fill=255
        )
    
    # Apply mask
    img.putalpha(mask)
    
    # Draw border
    draw_rounded_rect_border(draw, padding, padding, size - padding, size - padding, 
                            corner_radius, (100, 120, 200, 255), max(1, size // 40))
    
    # Add EXIF text
    font = None
    font_size = size // 4
    
    # Try to load a good font
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Avenir.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
    
    # If no font found, create text without font
    if not font:
        # Simple text without fancy font
        text = "EXIF"
        # Estimate text size
        text_width = len(text) * (size // 8)
        text_height = size // 6
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 10
        
        # Draw simple text
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, fill=(0, 0, 0, 64))
        draw.text((x, y), text, fill=(255, 255, 255, 255))
    else:
        # Draw text with font
        text = "EXIF"
        
        # Get text size using different method based on Pillow version
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(text, font=font)
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 10
        
        # Draw text shadow
        shadow_offset = max(1, size // 50)
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        # Add small "Tool" text below
        small_font = None
        small_font_size = size // 8
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    small_font = ImageFont.truetype(font_path, small_font_size)
                    break
                except:
                    continue
        
        if small_font:
            small_text = "Tool"
            try:
                bbox = draw.textbbox((0, 0), small_text, font=small_font)
                small_text_width = bbox[2] - bbox[0]
            except AttributeError:
                small_text_width, _ = draw.textsize(small_text, font=small_font)
            
            x = (size - small_text_width) // 2
            y = y + text_height + size // 20
            
            draw.text((x, y), small_text, font=small_font, fill=(200, 200, 255, 255))
    
    # Add subtle shine effect
    shine = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shine_draw = ImageDraw.Draw(shine)
    
    # Draw elliptical shine
    shine_draw.ellipse(
        [(padding + size//10, padding + size//10), 
         (size - padding - size//5, size//2)],
        fill=(255, 255, 255, 30)
    )
    
    # Composite shine onto main image
    img = Image.alpha_composite(img, shine)
    
    return img

def draw_rounded_rect_border(draw, x1, y1, x2, y2, radius, color, width):
    """Draw a rounded rectangle border"""
    # Draw the border using multiple rectangles or rounded rectangles
    if hasattr(draw, 'rounded_rectangle'):
        for i in range(width):
            draw.rounded_rectangle(
                [(x1 + i, y1 + i), (x2 - i, y2 - i)],
                radius=max(1, radius - i),
                outline=color,
                width=1
            )
    else:
        # Simple rectangle for older versions
        for i in range(width):
            draw.rectangle(
                [(x1 + i, y1 + i), (x2 - i, y2 - i)],
                outline=color,
                width=1
            )

def generate_iconset():
    """Generate all required icon sizes for macOS"""
    sizes = [
        (16, "16x16"),
        (32, "16x16@2x"),
        (32, "32x32"),
        (64, "32x32@2x"),
        (128, "128x128"),
        (256, "128x128@2x"),
        (256, "256x256"),
        (512, "256x256@2x"),
        (512, "512x512"),
        (1024, "512x512@2x")
    ]
    
    # Create iconset directory
    iconset_dir = "ExifToolGUI.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    print("Generating icon files...")
    
    for size, name in sizes:
        try:
            img = create_icon_image(size)
            filename = f"icon_{name}.png"
            filepath = os.path.join(iconset_dir, filename)
            img.save(filepath, "PNG")
            print(f"  Created {filename}")
        except Exception as e:
            print(f"  Error creating {filename}: {str(e)}")
            # Create a simple colored square as fallback
            img = Image.new('RGBA', (size, size), (40, 60, 140, 255))
            draw = ImageDraw.Draw(img)
            # Add a simple X pattern
            draw.line([(0, 0), (size, size)], fill=(255, 255, 255, 128), width=max(1, size//20))
            draw.line([(0, size), (size, 0)], fill=(255, 255, 255, 128), width=max(1, size//20))
            filepath = os.path.join(iconset_dir, filename)
            img.save(filepath, "PNG")
            print(f"  Created fallback {filename}")
    
    # Convert to .icns file
    print("\nConverting to .icns format...")
    try:
        subprocess.run([
            "iconutil", "-c", "icns", iconset_dir, "-o", "icon.icns"
        ], check=True)
        print("✓ Successfully created icon.icns")
        
        # Clean up iconset directory
        import shutil
        shutil.rmtree(iconset_dir)
        print("✓ Cleaned up temporary files")
        
    except subprocess.CalledProcessError:
        print("✗ Error: Failed to create .icns file")
        print("  Make sure you have Xcode command line tools installed")
        sys.exit(1)
    except FileNotFoundError:
        print("✗ Error: iconutil not found")
        print("  Install Xcode command line tools: xcode-select --install")
        sys.exit(1)

if __name__ == "__main__":
    print("ExifTool GUI Icon Generator")
    print("==========================\n")
    
    # Check for required module
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: Pillow is required")
        print("Install with: pip install Pillow")
        sys.exit(1)
    
    # Check Pillow version
    import PIL
    print(f"Using Pillow version: {PIL.__version__}")
    
    generate_iconset()
    
    print("\nDone! Use icon.icns in your build process.")