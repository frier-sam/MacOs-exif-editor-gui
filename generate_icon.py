#!/usr/bin/env python3
"""
Generate app icon for ExifTool GUI
Creates a modern icon with gradient and text
"""

from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
import sys

def create_simple_icon(size):
    """Create a simple icon without text as fallback"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Simple gradient background
    padding = size // 8
    for y in range(padding, size - padding):
        progress = (y - padding) / (size - 2 * padding)
        r = int(20 + progress * 40)
        g = int(30 + progress * 20)
        b = int(80 + progress * 60)
        draw.rectangle([(padding, y), (size - padding, y)], fill=(r, g, b, 255))
    
    # Add a simple pattern to indicate it's EXIF related
    center_x = size // 2
    center_y = size // 2
    radius = size // 4
    
    # Draw a camera-like icon
    draw.ellipse(
        [(center_x - radius, center_y - radius), 
         (center_x + radius, center_y + radius)],
        outline=(255, 255, 255, 255),
        width=max(1, size // 20)
    )
    
    # Inner circle
    inner_radius = radius // 2
    draw.ellipse(
        [(center_x - inner_radius, center_y - inner_radius), 
         (center_x + inner_radius, center_y + inner_radius)],
        outline=(255, 255, 255, 200),
        width=max(1, size // 30)
    )
    
    return img

def create_icon_image(size):
    """Create an icon image at the specified size"""
    try:
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
            # Fallback for older Pillow versions - simple rectangle
            mask_draw.rectangle(
                [(padding, padding), (size - padding, size - padding)],
                fill=255
            )
        
        # Apply mask
        img.putalpha(mask)
        
        # Try to add text, but skip if fonts cause issues
        try:
            # Simple text without loading fonts - just use basic drawing
            text = "EXIF"
            # Calculate approximate text position
            text_x = size // 3
            text_y = size // 3
            
            # Draw each letter manually with lines (simple approach)
            letter_size = size // 8
            line_width = max(1, size // 40)
            
            # E
            x_offset = text_x
            draw.line([(x_offset, text_y), (x_offset, text_y + letter_size)], fill=(255, 255, 255), width=line_width)
            draw.line([(x_offset, text_y), (x_offset + letter_size//2, text_y)], fill=(255, 255, 255), width=line_width)
            draw.line([(x_offset, text_y + letter_size//2), (x_offset + letter_size//2, text_y + letter_size//2)], fill=(255, 255, 255), width=line_width)
            draw.line([(x_offset, text_y + letter_size), (x_offset + letter_size//2, text_y + letter_size)], fill=(255, 255, 255), width=line_width)
            
            # X
            x_offset += letter_size
            draw.line([(x_offset, text_y), (x_offset + letter_size//2, text_y + letter_size)], fill=(255, 255, 255), width=line_width)
            draw.line([(x_offset + letter_size//2, text_y), (x_offset, text_y + letter_size)], fill=(255, 255, 255), width=line_width)
            
            # I
            x_offset += letter_size
            draw.line([(x_offset + letter_size//4, text_y), (x_offset + letter_size//4, text_y + letter_size)], fill=(255, 255, 255), width=line_width)
            
            # F
            x_offset += letter_size
            draw.line([(x_offset, text_y), (x_offset, text_y + letter_size)], fill=(255, 255, 255), width=line_width)
            draw.line([(x_offset, text_y), (x_offset + letter_size//2, text_y)], fill=(255, 255, 255), width=line_width)
            draw.line([(x_offset, text_y + letter_size//2), (x_offset + letter_size//2, text_y + letter_size//2)], fill=(255, 255, 255), width=line_width)
            
        except Exception as e:
            print(f"  Warning: Could not draw text for size {size}: {e}")
        
        # Add subtle shine effect
        shine = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        shine_draw = ImageDraw.Draw(shine)
        
        # Draw elliptical shine
        try:
            shine_draw.ellipse(
                [(padding + size//10, padding + size//10), 
                 (size - padding - size//5, size//2)],
                fill=(255, 255, 255, 30)
            )
            # Composite shine onto main image
            img = Image.alpha_composite(img, shine)
        except:
            pass
        
        return img
        
    except Exception as e:
        print(f"  Warning: Error creating icon size {size}, using simple fallback: {e}")
        return create_simple_icon(size)

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
        filename = f"icon_{name}.png"
        filepath = os.path.join(iconset_dir, filename)
        
        try:
            img = create_icon_image(size)
            img.save(filepath, "PNG")
            print(f"  Created {filename}")
        except Exception as e:
            print(f"  Error creating {filename}: {str(e)}")
            # Create a simple colored square as fallback
            try:
                img = Image.new('RGBA', (size, size), (40, 60, 140, 255))
                draw = ImageDraw.Draw(img)
                # Add a simple pattern
                for i in range(0, size, size//4):
                    draw.line([(i, 0), (i, size)], fill=(60, 80, 160, 128), width=1)
                    draw.line([(0, i), (size, i)], fill=(60, 80, 160, 128), width=1)
                img.save(filepath, "PNG")
                print(f"  Created fallback {filename}")
            except Exception as e2:
                print(f"  Failed to create fallback for {filename}: {e2}")
    
    # Convert to .icns file
    print("\nConverting to .icns format...")
    try:
        # Check if iconutil exists first
        result = subprocess.run(['which', 'iconutil'], capture_output=True, text=True)
        if result.returncode != 0:
            print("✗ Error: iconutil not found")
            print("  Creating placeholder icon.icns file")
            # Create a placeholder icon.icns file
            with open('icon.icns', 'wb') as f:
                f.write(b'icns')  # Minimal icns header
            return
        
        # Run iconutil
        result = subprocess.run([
            "iconutil", "-c", "icns", iconset_dir, "-o", "icon.icns"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully created icon.icns")
            
            # Clean up iconset directory
            import shutil
            shutil.rmtree(iconset_dir)
            print("✓ Cleaned up temporary files")
        else:
            print(f"✗ Error creating .icns file: {result.stderr}")
            print("  Creating placeholder icon.icns file")
            with open('icon.icns', 'wb') as f:
                f.write(b'icns')
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print("  Creating placeholder icon.icns file")
        with open('icon.icns', 'wb') as f:
            f.write(b'icns')

if __name__ == "__main__":
    print("ExifTool GUI Icon Generator")
    print("==========================\n")
    
    # Check for required module
    try:
        from PIL import Image, ImageDraw, ImageFont
        import PIL
        print(f"Using Pillow version: {PIL.__version__}")
    except ImportError:
        print("Error: Pillow is required")
        print("Install with: pip install Pillow")
        # Create a minimal icon.icns file so build can continue
        with open('icon.icns', 'wb') as f:
            f.write(b'icns')
        sys.exit(0)  # Exit successfully to not break the build
    
    generate_iconset()
    
    print("\nDone! icon.icns created.")