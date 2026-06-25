import os
import shutil
from pathlib import Path

# Directories
TRAINING_DIR = Path("data/training_images")
REFERENCE_DIR = Path("data/reference_images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def load_training_images(source_dir: Path = TRAINING_DIR) -> list[Path]:
    """Return a sorted list of image paths found in source_dir."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Training image directory not found: {source_dir}")

    images = sorted(
        p for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    print(f"Found {len(images)} training image(s) in '{source_dir}'.")
    return images


def copy_to_reference(images: list[Path], dest_dir: Path = REFERENCE_DIR) -> None:
    """Copy a list of image files into the reference_images directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for img in images:
        dest = dest_dir / img.name
        shutil.copy2(img, dest)
        print(f"Copied: {img.name} -> {dest}")


def main():
    print("=== Loading Training Images ===")
    images = load_training_images()

    if not images:
        print("No images found. Exiting.")
        return

    print(f"\nCopying {len(images)} image(s) to reference directory...")
    copy_to_reference(images)
    print("\nDone.")


if __name__ == "__main__":
    main()
