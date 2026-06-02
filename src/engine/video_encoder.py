"""
src/engine/video_encoder.py
Streams BGR frames from an iterator into an MP4 file using OpenCV VideoWriter.
Frames are written one-at-a-time so RAM usage stays near O(1).
"""

import cv2
import numpy as np
import os
from typing import Iterator, Tuple, Optional, Callable


class VideoEncoder:
    """Encodes a stream of BGR numpy frames into an MP4 file."""

    def encode(
        self,
        frame_iter: Iterator[Tuple[np.ndarray, int, str]],
        output_path: str,
        fps: int,
        width: int,
        height: int,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> str:
        """
        Write frames from frame_iter to an MP4 file.

        Args:
            frame_iter  : yields (bgr_ndarray, render_pct, status_msg)
            output_path : destination .mp4 path
            fps         : frames per second
            width       : expected frame width  (frames are resized if different)
            height      : expected frame height
            on_progress : callback(pct, message) – called after every frame write

        Returns:
            Absolute path to the created file.

        Raises:
            RuntimeError  if VideoWriter cannot be opened.
            ValueError    if no frames were written.
        """
        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))

        if not writer.isOpened():
            raise RuntimeError(
                f"OpenCV VideoWriter could not open '{output_path}'. "
                "Check that the output directory is writable."
            )

        frame_count = 0
        try:
            for frame_bgr, pct, msg in frame_iter:
                # Guard: resize if dimensions differ (safety net)
                fh, fw = frame_bgr.shape[:2]
                if fw != width or fh != height:
                    frame_bgr = cv2.resize(frame_bgr, (width, height),
                                           interpolation=cv2.INTER_LINEAR)

                writer.write(frame_bgr)
                frame_count += 1

                if on_progress:
                    on_progress(pct, msg)

        finally:
            writer.release()

        if frame_count == 0:
            raise ValueError("No frames were written — the frame iterator was empty.")

        return os.path.abspath(output_path)
