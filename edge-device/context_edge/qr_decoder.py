# QR code detection and decoding

import cv2
from typing import Optional, Tuple

class QRDecoder:
    def __init__(self):
        self.detector = cv2.QRCodeDetector()

    def detect_and_decode(self, frame) -> Optional[str]:
        """
        Detect QR code in frame and return decoded string
        """
        data, bbox, _ = self.detector.detectAndDecode(frame)
        
        if data:
            return data.strip()
        
        return None

    def detect_qr_position(self, frame) -> Optional[Tuple]:
        """
        Detect QR code position for spatial markers
        """
        data, bbox, _ = self.detector.detectAndDecode(frame)
        
        if bbox is not None:
            # Return bounding box coordinates
            return tuple(bbox[0])  # Top-left corner
        
        return None