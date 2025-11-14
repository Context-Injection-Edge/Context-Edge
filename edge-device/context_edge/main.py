# Main entry point for edge device

from .vision_engine import VisionEngine
from .qr_decoder import QRDecoder
from .context_injector import ContextInjectionModule
from .ldo_generator import LDOGenerator
import time
import os

def main():
    # Configuration
    context_service_url = os.getenv("CONTEXT_SERVICE_URL", "http://localhost:8000")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    
    # Initialize components
    vision = VisionEngine()
    qr_decoder = QRDecoder()
    cim = ContextInjectionModule(context_service_url, redis_host)
    ldo_gen = LDOGenerator()
    
    # Start camera
    if not vision.start_capture():
        print("Failed to start camera")
        return
    
    print("Context Edge Edge Device started...")
    
    try:
        for frame in vision.stream_frames():
            # Detect QR code
            cid = qr_decoder.detect_and_decode(frame)
            
            # Mock sensor data (in real implementation, this would come from sensors)
            sensor_data = {
                "temperature": 25.5,
                "pressure": 1013.25,
                "timestamp": time.time()
            }
            
            # Inject context
            ldo = cim.inject_context(sensor_data, cid)
            
            # Generate LDO if we have context
            if ldo["context_metadata"]:
                ldo_id = ldo_gen.generate_ldo(ldo, frame)
                print(f"Generated LDO: {ldo_id}")
            
            # Small delay to prevent overwhelming
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        vision.stop_capture()

if __name__ == "__main__":
    main()