# Main entry point for edge device

from .vision_engine import VisionEngine
from .qr_decoder import QRDecoder
from .context_injector import ContextInjectionModule
from .ldo_generator import LDOGenerator
from .opcua_protocol import OPCUAProtocol
from .modbus_protocol import ModbusProtocol
import time
import os

def main():
    # Configuration
    context_service_url = os.getenv("CONTEXT_SERVICE_URL", "http://localhost:8000")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    protocol_type = os.getenv("PROTOCOL_TYPE", "mock")  # mock, opcua, modbus

    # Initialize data protocol
    data_protocol = None
    if protocol_type == "opcua":
        opcua_url = os.getenv("OPCUA_URL", "opc.tcp://localhost:4840")
        node_mappings = {
            "temperature": "ns=2;s=Temperature",
            "pressure": "ns=2;s=Pressure",
            "vibration": "ns=2;s=Vibration"
        }
        data_protocol = OPCUAProtocol(opcua_url, node_mappings)
    elif protocol_type == "modbus":
        modbus_host = os.getenv("MODBUS_HOST", "localhost")
        register_mappings = {
            "temperature": {"address": 0, "type": "holding", "count": 1},
            "pressure": {"address": 1, "type": "holding", "count": 1},
            "vibration": {"address": 2, "type": "holding", "count": 1}
        }
        data_protocol = ModbusProtocol(modbus_host, register_mappings=register_mappings)

    # Initialize components
    vision = VisionEngine()
    qr_decoder = QRDecoder()
    cim = ContextInjectionModule(context_service_url, redis_host, data_protocol=data_protocol)
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

            # Inject context (sensor data comes from protocol)
            ldo = cim.inject_context(detected_cid=cid)

            # Generate LDO if we have context
            if ldo["context_metadata"]:
                ldo_id = ldo_gen.generate_ldo(ldo, frame)
                print(f"Generated LDO: {ldo_id}")
                print(f"Industrial Context: {ldo.get('industrial_context', {})}")

            # Small delay to prevent overwhelming
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        vision.stop_capture()

if __name__ == "__main__":
    main()