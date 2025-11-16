"""
Camera Stream Input Module
Captures video, decodes QR codes, extracts CID, saves video clips
"""

import cv2
import time
import os
from pyzbar import pyzbar
from typing import Optional, Callable
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CameraStreamInput:
    """
    Camera input module for QR code scanning with video clip capture
    Handles video streaming, QR decoding, and video clip recording
    """

    def __init__(
        self,
        camera_index: int = 0,
        scan_interval: float = 1.0,
        video_duration: float = 5.0,
        video_buffer_seconds: float = 2.0,
        on_cid_detected: Optional[Callable[[str, Optional[str]], None]] = None
    ):
        """
        Initialize camera stream input

        Args:
            camera_index: Camera device index (0 for default)
            scan_interval: Minimum seconds between duplicate CID detections
            video_duration: Duration of video clip to capture (seconds)
            video_buffer_seconds: Seconds of video to capture BEFORE QR detection
            on_cid_detected: Callback function when CID is detected (cid, video_path)
        """
        self.camera_index = camera_index
        self.scan_interval = scan_interval
        self.video_duration = video_duration
        self.video_buffer_seconds = video_buffer_seconds
        self.on_cid_detected = on_cid_detected
        self.last_cid = None
        self.last_scan_time = 0
        self.cap = None

        # Video recording setup
        self.video_output_dir = Path(os.getenv("VIDEO_OUTPUT_DIR", "/tmp/context-edge-videos"))
        self.video_output_dir.mkdir(parents=True, exist_ok=True)

        # Circular buffer for pre-QR detection video
        self.frame_buffer = []
        self.fps = 30  # Will be updated when camera opens

    def start(self):
        """Start camera stream and QR scanning with video recording"""
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            logger.error(f"❌ Failed to open camera at index {self.camera_index}")
            raise RuntimeError(f"Cannot open camera {self.camera_index}")

        # Get actual FPS
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30

        logger.info(f"✅ Camera opened successfully (index: {self.camera_index}, FPS: {self.fps})")
        logger.info(f"📹 Video clip duration: {self.video_duration}s (buffer: {self.video_buffer_seconds}s)")
        logger.info("🔍 Scanning for QR codes...")

        # Calculate buffer size (frames to keep before QR detection)
        buffer_size = int(self.fps * self.video_buffer_seconds)

        try:
            while True:
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning("⚠️  Failed to capture frame")
                    time.sleep(0.1)
                    continue

                # Add frame to circular buffer
                self.frame_buffer.append(frame.copy())
                if len(self.frame_buffer) > buffer_size:
                    self.frame_buffer.pop(0)

                # Decode QR codes in frame
                barcodes = pyzbar.decode(frame)

                for barcode in barcodes:
                    cid = barcode.data.decode('utf-8')
                    self._handle_cid_detected(cid, frame)

                # Small delay (~30 FPS)
                time.sleep(0.033)

        except KeyboardInterrupt:
            logger.info("\\n⏹️  Stopping camera stream...")
        finally:
            self.stop()

    def stop(self):
        """Stop camera stream"""
        if self.cap:
            self.cap.release()
            logger.info("✅ Camera released")

    def _handle_cid_detected(self, cid: str, current_frame):
        """
        Handle CID detection with debouncing and video clip recording

        Args:
            cid: Detected Context ID
            current_frame: Current video frame where QR was detected
        """
        current_time = time.time()

        # Debounce - don't process same CID too quickly
        if cid == self.last_cid and (current_time - self.last_scan_time) < self.scan_interval:
            return

        self.last_cid = cid
        self.last_scan_time = current_time

        logger.info(f"📷 QR Code detected: {cid}")
        logger.info(f"🎬 Recording video clip...")

        # Record video clip (pre-buffer + post-detection)
        video_path = self._record_video_clip(cid, current_frame)

        logger.info(f"✅ Video saved: {video_path}")

        # Call callback with CID and video path
        if self.on_cid_detected:
            self.on_cid_detected(cid, video_path)

    def _record_video_clip(self, cid: str, current_frame) -> str:
        """
        Record video clip around QR detection moment

        Args:
            cid: Context ID (for filename)
            current_frame: Current frame where QR was detected

        Returns:
            Path to saved video file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"{cid}_{timestamp}.mp4"
        video_path = self.video_output_dir / video_filename

        # Video codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        height, width = current_frame.shape[:2]

        out = cv2.VideoWriter(str(video_path), fourcc, self.fps, (width, height))

        # Write pre-buffer frames (frames BEFORE QR detection)
        for frame in self.frame_buffer:
            out.write(frame)

        # Write current frame
        out.write(current_frame)

        # Continue recording for remaining duration
        frames_to_record = int(self.fps * (self.video_duration - self.video_buffer_seconds))

        for _ in range(frames_to_record):
            ret, frame = self.cap.read()
            if ret:
                out.write(frame)
            else:
                break

        out.release()

        return str(video_path)
