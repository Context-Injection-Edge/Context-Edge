"""
Camera Stream Input Module
Captures video, decodes QR codes, extracts CID
"""

import cv2
import time
from pyzbar import pyzbar
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class CameraStreamInput:
    """
    Camera input module for QR code scanning
    Handles video streaming and QR decoding
    """

    def __init__(
        self,
        camera_index: int = 0,
        scan_interval: float = 1.0,
        on_cid_detected: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize camera stream input

        Args:
            camera_index: Camera device index (0 for default)
            scan_interval: Minimum seconds between duplicate CID detections
            on_cid_detected: Callback function when CID is detected
        """
        self.camera_index = camera_index
        self.scan_interval = scan_interval
        self.on_cid_detected = on_cid_detected
        self.last_cid = None
        self.last_scan_time = 0
        self.cap = None

    def start(self):
        """Start camera stream and QR scanning"""
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            logger.error(f"❌ Failed to open camera at index {self.camera_index}")
            raise RuntimeError(f"Cannot open camera {self.camera_index}")

        logger.info(f"✅ Camera opened successfully (index: {self.camera_index})")
        logger.info("🔍 Scanning for QR codes...")

        try:
            while True:
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning("⚠️  Failed to capture frame")
                    time.sleep(0.1)
                    continue

                # Decode QR codes in frame
                barcodes = pyzbar.decode(frame)

                for barcode in barcodes:
                    cid = barcode.data.decode('utf-8')
                    self._handle_cid_detected(cid)

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

    def _handle_cid_detected(self, cid: str):
        """
        Handle CID detection with debouncing

        Args:
            cid: Detected Context ID
        """
        current_time = time.time()

        # Debounce - don't process same CID too quickly
        if cid == self.last_cid and (current_time - self.last_scan_time) < self.scan_interval:
            return

        self.last_cid = cid
        self.last_scan_time = current_time

        logger.info(f"📷 QR Code detected: {cid}")

        # Call callback if provided
        if self.on_cid_detected:
            self.on_cid_detected(cid)
