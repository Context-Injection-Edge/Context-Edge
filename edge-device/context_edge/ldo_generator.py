# LDO Generator - creates Labeled Data Objects

import json
import cv2
import os
from typing import Dict, Any, Optional
from datetime import datetime

class LDOGenerator:
    def __init__(self, output_dir: str = "ldo_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_ldo(self, ldo_data: Dict[str, Any], frame: Optional = None, video_writer: Optional = None) -> str:
        """
        Generate LDO: JSON metadata + video/image
        Returns LDO ID
        """
        ldo_id = f"ldo_{int(datetime.now().timestamp() * 1000)}"
        ldo_path = os.path.join(self.output_dir, ldo_id)
        os.makedirs(ldo_path, exist_ok=True)

        # Save metadata
        metadata_file = os.path.join(ldo_path, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(ldo_data, f, indent=2, default=str)

        # Save frame/image if provided
        if frame is not None:
            image_file = os.path.join(ldo_path, "frame.jpg")
            cv2.imwrite(image_file, frame)

        # If video writer, save video segment
        if video_writer:
            # Assuming video_writer is a cv2.VideoWriter
            # This would need to be managed externally for video segments
            pass

        return ldo_id

    def create_video_segment(self, frames: list, fps: int = 30) -> str:
        """
        Create video segment from frames
        """
        if not frames:
            return None

        height, width = frames[0].shape[:2]
        video_path = os.path.join(self.output_dir, f"segment_{int(datetime.now().timestamp())}.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        
        for frame in frames:
            writer.write(frame)
        
        writer.release()
        return video_path