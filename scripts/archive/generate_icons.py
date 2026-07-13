"""
Module: scripts.archive.generate_icons

Purpose:
    Provide generate_icons.py functionality.

Subscribes to:
    None

Publishes:
    None

"""
import os
from pathlib import Path
from PIL import Image

def generate_icons():
    base_dir = Path(__file__).parent.parent
    master_logo_path = base_dir / "web" / "asset" / "logos" / "lunawave_master.png"
    icons_dir = base_dir / "web" / "static" / "icons"
    
    print(f"Master logo path: {master_logo_path.resolve()}")
    if not master_logo_path.exists():
        print(f"Error: Master logo not found at {master_logo_path}")
        return False
        
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Open master logo
    img = Image.open(master_logo_path)
    
    # Save 192x192 icon
    icon_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    icon_192_path = icons_dir / "icon-192.png"
    icon_192.save(icon_192_path, "PNG")
    print(f"Generated 192x192 icon at: {icon_192_path.resolve()}")
    
    # Save 512x512 icon
    icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    icon_512_path = icons_dir / "icon-512.png"
    icon_512.save(icon_512_path, "PNG")
    print(f"Generated 512x512 icon at: {icon_512_path.resolve()}")
    
    return True

if __name__ == "__main__":
    generate_icons()