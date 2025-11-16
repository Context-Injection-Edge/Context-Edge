"""
RFID Reader Input Module
Reads RFID tags to extract CID
"""

import time
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class RFIDReaderInput:
    """
    RFID reader input module
    Reads RFID tags and extracts CID
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        scan_interval: float = 1.0,
        on_cid_detected: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize RFID reader

        Args:
            port: Serial port for RFID reader
            baudrate: Serial baudrate
            scan_interval: Minimum seconds between duplicate reads
            on_cid_detected: Callback function when CID is detected
        """
        self.port = port
        self.baudrate = baudrate
        self.scan_interval = scan_interval
        self.on_cid_detected = on_cid_detected
        self.last_cid = None
        self.last_scan_time = 0

    def start(self):
        """Start RFID reader"""
        logger.info(f"🔖 RFID Reader initialized on {self.port}")
        logger.info("⚠️  RFID module not yet implemented - placeholder only")

        # TODO: Implement actual RFID reading
        # import serial
        # self.serial = serial.Serial(self.port, self.baudrate)
        #
        # while True:
        #     data = self.serial.readline()
        #     cid = self._parse_rfid_data(data)
        #     if cid:
        #         self._handle_cid_detected(cid)

    def stop(self):
        """Stop RFID reader"""
        logger.info("✅ RFID reader stopped")

    def _handle_cid_detected(self, cid: str):
        """Handle CID detection with debouncing"""
        current_time = time.time()

        if cid == self.last_cid and (current_time - self.last_scan_time) < self.scan_interval:
            return

        self.last_cid = cid
        self.last_scan_time = current_time

        logger.info(f"🔖 RFID tag detected: {cid}")

        if self.on_cid_detected:
            self.on_cid_detected(cid)
