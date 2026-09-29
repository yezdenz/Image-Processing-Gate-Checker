"""Dataset Preparation and ROI Cropping Tool.

Processes raw CCTV captures from data/raw/ by extracting the gate Region of Interest (ROI),
resizing to 224x224, and preparing them for classification labeling or split generation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def crop_roi(
    image: np.ndarray,
    roi_coords: list[list[float]],
    target_size: tuple[int, int] = (224, 224),
) -> np.ndarray:
    """Crop polygonal or rectangular ROI and resize.

    Args:
        image: Source full-frame BGR image.
        roi_coords: Normalized coordinates [[x1, y1], [x2, y2], ...].
        target_size: Output resolution (width, height).

    Returns:
        Cropped and resized ROI image.
    """
    h, w = image.shape[:2]
    pts = np.array([[int(p[0] * w), int(p[1] * h)] for p in roi_coords], dtype=np.int32)

    # Bounding box of the polygon
    x, y, bw, bh = cv2.boundingRect(pts)
    x = max(0, x)
    y = max(0, y)
    bw = min(bw, w - x)
    bh = min(bh, h - y)

    cropped = image[y : y + bh, x : x + bw]
    resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)
    return resized


def process_raw_dataset(
    raw_dir: Path,
    output_dir: Path,
    roi_polygon: list[list[float]],
    target_size: tuple[int, int] = (224, 224),
) -> int:
    """Iterate over all raw captures and generate cropped ROI frames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    processed_count = 0

    raw_images = [p for p in raw_dir.glob("*") if p.suffix.lower() in image_extensions]
    print(f"Found {len(raw_images)} raw images in {raw_dir}")

    for img_path in raw_images:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        roi_crop = crop_roi(img, roi_polygon, target_size)
        out_name = f"roi_{img_path.name}"
        out_path = output_dir / out_name
        cv2.imwrite(str(out_path), roi_crop)
        processed_count += 1

    print(f"Processed and cropped {processed_count} ROI patches to {output_dir}")
    return processed_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop gate ROIs from raw CCTV captures")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"), help="Directory containing raw images")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/staging"), help="Output directory for cropped ROIs")
    parser.add_argument(
        "--roi",
        type=str,
        default="[[0.15, 0.20], [0.85, 0.20], [0.85, 0.85], [0.15, 0.85]]",
        help="JSON string of normalized polygon vertices",
    )
    args = parser.parse_args()

    polygon = json.loads(args.roi)
    process_raw_dataset(raw_dir=args.raw_dir, output_dir=args.output_dir, roi_polygon=polygon)


if __name__ == "__main__":
    main()
