import os
from PIL import Image, ExifTags
import pillow_heif

import random

pillow_heif.register_heif_opener()

print("Gallery files prep .... ")

folder_path = "2025"  # Your folder path

thumb_folder = os.path.join(folder_path, "thumbnails")
web_folder = os.path.join(folder_path, "web")

# Create folders if not exist
os.makedirs(thumb_folder, exist_ok=True)
os.makedirs(web_folder, exist_ok=True)

THUMB_SIZE = (600, 600)
WEB_SIZE = (1200, 1200)

files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
# files.sort()
random.shuffle(files)  # <- randomize order

# Mapping EXIF orientation to PIL transpose method
EXIF_ORIENTATION_TAG = next(k for k, v in ExifTags.TAGS.items() if v == "Orientation")
ORIENTATION_TRANSPOSE = {
    3: Image.Transpose.ROTATE_180,
    6: Image.Transpose.ROTATE_270,
    8: Image.Transpose.ROTATE_90,
}

def auto_rotate(image):
    try:
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(EXIF_ORIENTATION_TAG)
            if orientation in ORIENTATION_TRANSPOSE:
                image = image.transpose(ORIENTATION_TRANSPOSE[orientation])
    except Exception as e:
        print(f"  - EXIF rotation skipped: {e}")
    return image

index = 1  # Start numbering from 1

for filename in files:
    old_path = os.path.join(folder_path, filename)
    try:
        img = Image.open(old_path)

        # Auto-rotate based on EXIF
        img = auto_rotate(img)

        if img.mode != "RGB":
            img = img.convert("RGB")

        # Create and save thumbnail
        thumb_img = img.copy()
        thumb_img.thumbnail(THUMB_SIZE)
        thumb_name = f"{index}_thumb.jpg"
        thumb_path = os.path.join(thumb_folder, thumb_name)
        thumb_img.save(thumb_path, "JPEG", quality=85)

        # Create and save web-sized image
        web_img = img.copy()
        web_img.thumbnail(WEB_SIZE)
        web_name = f"{index}.jpg"
        web_path = os.path.join(web_folder, web_name)
        web_img.save(web_path, "JPEG", quality=85)

        print(f"Processed '{filename}' -> thumbnail: '{thumb_name}', web: '{web_name}'")
        index += 1  # Only increment if success

    except Exception as e:
        print(f"Skipping '{filename}': {e}")

print("Processing completed.")
