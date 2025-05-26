#!/usr/bin/env python3
"""
Generate app icon for ExifTool GUI
Creates a modern icon with gradient and text
"""

from PIL import Image, ImageDraw, ImageFont
import os
import subprocess

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
    mask_draw.rounded_rectangle(
        [(padding, padding), (size - padding, size - padding)],
        radius=corner_radius,
        fill=255
    )
    
    # Apply mask
    img.putalpha(mask)
    
    # Draw border
    draw_rounded_rect_border(draw, padding, padding, size - padding, size - padding, 
                            corner_radius, (100, 120, 200, 255), size // 40)
    
    # Add EXIF text
    try:
        # Try to use system font
        font_size = size // 4
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "EXIF" text
    text = "EXIF"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size // 10
    
    # Draw text shadow
    shadow_offset = size // 50
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # Add small "Tool" text below
    try:
        small_font_size = size // 8
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", small_font_size)
    except:
        small_font = font
    
    small_text = "Tool"
    bbox = draw.textbbox((0, 0), small_text, font=small_font)
    small_text_width = bbox[2] - bbox[0]
    
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
    # Draw the border using multiple rounded rectangles
    for i in range(width):
        draw.rounded_rectangle(
            [(x1 + i, y1 + i), (x2 - i, y2 - i)],
            radius=radius - i,
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
        img = create_icon_image(size)
        filename = f"icon_{name}.png"
        filepath = os.path.join(iconset_dir, filename)
        img.save(filepath, "PNG")
        print(f"  Created {filename}")
    
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
    except FileNotFoundError:
        print("✗ Error: iconutil not found")
        print("  Install Xcode command line tools: xcode-select --install")

if __name__ == "__main__":
    print("ExifTool GUI Icon Generator")
    print("==========================\n")
    
    # Check for required module
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: Pillow is required")
        print("Install with: pip install Pillow")
        exit(1)
    
    generate_iconset()
    
    print("\nDone! Use icon.icns in your build process.")