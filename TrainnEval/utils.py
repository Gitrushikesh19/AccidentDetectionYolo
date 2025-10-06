import socket
import uuid
from pathlib import Path

def get_device_id():
    try:
        # hostname is usually unique enough per device
        hostname = socket.gethostname()
        return hostname
    except Exception:
        # fallback: use MAC address as hex string
        mac = uuid.getnode()
        return f"mac-{mac:x}"

def rename_images(folder_path, prefix=get_device_id):
    folder = Path(folder_path)
    images = sorted([p for p in folder.glob("*.jpg")])  # you can add *.png etc.

    for idx, img_path in enumerate(images, start=1):
        # embed device_id in the filename
        new_name = f"{prefix}_{idx}.jpg"
        new_path = img_path.with_name(new_name)
        img_path.rename(new_path)
        print(f"[INFO] Renamed {img_path.name} -> {new_name}")

rename_images(r"D:\Datasets\Accident_Detection\train\images", prefix=get_device_id)

valid_ext = {'.jpg'}

# Use this if the directory and files are structured this way
def gather_images(path):
    p = Path(path)

    if not p.exists():
        return []

    if p.is_file():
        if p.suffix.lower() in valid_ext:
            return [str(p.resolve())]
        else:
            return []

    children_names = {c.name.lower() for c in p.iterdir() if c.is_dir()}
    dataset_subdirs = {'train', 'val', 'test'}
    gathered_images = []

    if dataset_subdirs & children_names:
        for sub in ('test', 'val', 'train'):
            subdir = p / sub
            if subdir.exists() and subdir.is_dir():
                images_folder = None
                if (subdir / 'images').exists():
                    images_folder = subdir / 'images'
                else:
                    images_folder = subdir
                gathered_images.extend([str(img.resolve()) for img in images_folder.rglob('*') if img.suffix.lower() in valid_ext])

        gathered_images = sorted(set(gathered_images))
        return gathered_images
