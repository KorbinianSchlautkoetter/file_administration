import os
import shutil
from datetime import datetime
from pathlib import Path
import argparse
import exifread

def get_exif_date(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
        date_taken = tags.get("EXIF DateTimeOriginal")
        if date_taken:
            return datetime.strptime(str(date_taken), "%Y:%m:%d %H:%M:%S")
    return None

def get_file_dates(file_path):
    try:
        creation_date = datetime.fromtimestamp(os.path.getctime(file_path))
    except Exception:
        creation_date = None
    try:
        modified_date = datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception:
        modified_date = None
    return creation_date, modified_date

def get_file_size(file_path):
    return os.path.getsize(file_path)

def format_date(date):
    return date.strftime("%Y%m%d_%H%M%S")

def rename_file(src_path, dst_dir, base_name, extension):
    new_path = dst_dir / f"{base_name}{extension}"
    counter = 1
    while new_path.exists():
        if counter > 1:
            new_path = dst_dir / f"{base_name}_{counter}{extension}"
        else:
            new_path = dst_dir / f"{base_name}{extension}"
        counter += 1
    shutil.move(src_path, new_path)

def process_file(file_path, dst_dir):
    file_extension = file_path.suffix.lower()
    file_size = get_file_size(file_path)
    file_size_str = str(file_size)
    
    # Try to get EXIF date first
    date_taken = None
    if file_extension in ['.jpg', '.jpeg', '.tiff']:
        date_taken = get_exif_date(file_path)

    # Fallbacks for date
    if not date_taken:
        creation_date, modified_date = get_file_dates(file_path)
        date_taken = creation_date or modified_date
    
    # If date is still None, skip the file
    if not date_taken:
        print(f"Skipping {file_path} as no date could be determined.")
        return
    
    formatted_date = format_date(date_taken)

    # Check for specific indicators in the filename
    indicators = []
    if "screenshot" in file_path.name.lower():
        indicators.append("Screenshot")
    if "_whatsapp" in file_path.name.lower() or "-WA" in file_path.name:
        indicators.append("Whatsapp")
    if "signal" in file_path.name.lower():
        indicators.append("Signal")
    
    indicator_str = "_".join(indicators) if indicators else ""
    base_name = f"{formatted_date}_{file_size_str}"
    if indicator_str:
        base_name = f"{base_name}_{indicator_str}"
    
    rename_file(file_path, dst_dir, base_name, file_path.suffix)

def iterate_directory(src_dir, dst_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            file_path = Path(root) / file
            process_file(file_path, dst_dir)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Rename images and videos based on metadata. Remember running it on WSL the directory is stated as follows: python ./appCode/file_transformation_app/main.py "/mnt/c/Users/Korbinian/..."')
    parser.add_argument("directory", help="Directory to scan for images and videos.")
    args = parser.parse_args()

    src_dir = Path(args.directory)
    dst_dir = src_dir / "renamed_files"
    dst_dir.mkdir(exist_ok=True)

    iterate_directory(src_dir, dst_dir)
