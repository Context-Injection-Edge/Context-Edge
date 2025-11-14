# Vision engine for capturing video streams

import cv2
from typing import Generator, Optional

class VisionEngine:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None

    def start_capture(self) -> bool:
        """Start video capture from camera"""
        self.cap = cv2.VideoCapture(self.camera_index)
        return self.cap.isOpened()

    def stop_capture(self):
        """Stop video capture"""
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame(self) -> Optional:
        """Get next frame from camera"""
        if not self.cap:
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None

    def stream_frames(self) -> Generator:
        """Generator for streaming frames"""
        while self.cap and self.cap.isOpened():
            frame = self.get_frame()
            if frame is not None:
                yield frame
            else:
                break