"""RTSP Frame Capture Utility for Model Training.

Connects to the CCTV RTSP stream, captures frames at periodic intervals
or on manual keypress, and saves them to the data/raw directory.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path

import cv2
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()


def get_stream_url() -> str:
    """Build the authenticated RTSP stream URL from environment variables."""
    base_url = os.getenv("CCTV_RTSP_URL", "rtsp://192.168.1.4:554/stream1")
    username = os.getenv("CCTV_USERNAME", "")
    password = os.getenv("CCTV_PASSWORD", "")

    if username and password and not ("://" in base_url and "@" in base_url):
        prefix, host_part = base_url.split("://", 1)
        return f"{prefix}://{username}:{password}@{host_part}"
    return base_url


def mask_url(url: str) -> str:
    """Mask credentials in RTSP URL for safe console output."""
    import re
    return re.sub(r"(rtsp://)([^:]+):([^@]+)@", r"\1***:***@", url)


def capture_stream(
    output_dir: Path,
    interval_seconds: float = 5.0,
    max_frames: int | None = None,
    display: bool = True,
) -> None:
    """Capture frames from RTSP stream.

    Args:
        output_dir: Directory where raw images will be saved.
        interval_seconds: Seconds between automatic captures (0 for manual only).
        max_frames: Maximum number of frames to capture before stopping.
        display: Whether to show an interactive OpenCV preview window.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stream_url = get_stream_url()
    masked = mask_url(stream_url)

    print(f"Connecting to RTSP Stream: {masked}")
    # Force TCP transport via environment flag for OpenCV FFmpeg backend
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    if not cap.isOpened():
        print(f"Error: Unable to open RTSP stream at {masked}", file=sys.stderr)
        return

    print("Stream successfully connected.")
    if display:
        print("Controls: Press 'c' or 'SPACE' to capture frame, 'q' or 'ESC' to quit.")

    saved_count = 0
    last_capture_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Received empty frame or stream disconnected. Retrying...")
                time.sleep(1.0)
                continue

            current_time = time.time()
            trigger_capture = False

            if interval_seconds > 0 and (current_time - last_capture_time) >= interval_seconds:
                trigger_capture = True

            if display:
                preview = cv2.resize(frame, (960, 540))
                overlay_text = f"Saved: {saved_count} | Auto-interval: {interval_seconds}s"
                cv2.putText(
                    preview,
                    overlay_text,
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("CCTV Stream - Dataset Capture", preview)
                key = cv2.waitKey(1) & 0xFF

                if key in (ord("q"), 27):  # 'q' or ESC
                    print("Exiting capture loop...")
                    break
                elif key in (ord("c"), 32):  # 'c' or SPACE
                    trigger_capture = True

            if trigger_capture:
                timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"gate_raw_{timestamp_str}.jpg"
                file_path = output_dir / filename
                cv2.imwrite(str(file_path), frame)
                saved_count += 1
                last_capture_time = current_time
                print(f"[{saved_count}] Saved snapshot: {file_path.name}")

                if max_frames and saved_count >= max_frames:
                    print(f"Reached target frame limit ({max_frames}). Stopping.")
                    break

    except KeyboardInterrupt:
        print("\nCapture interrupted by user.")
    finally:
        cap.release()
        if display:
            cv2.destroyAllWindows()
        print(f"Finished. Total frames saved: {saved_count} to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture frames from CCTV RTSP stream for ML training.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("data/raw"),
        help="Directory to save raw frame images (default: data/raw)",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=5.0,
        help="Capture interval in seconds (default: 5.0, set 0 for manual only)",
    )
    parser.add_argument(
        "--max-frames",
        "-m",
        type=int,
        default=None,
        help="Maximum number of frames to capture (default: unlimited)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without displaying GUI preview window",
    )
    args = parser.parse_args()

    capture_stream(
        output_dir=args.output,
        interval_seconds=args.interval,
        max_frames=args.max_frames,
        display=not args.headless,
    )


if __name__ == "__main__":
    main()
