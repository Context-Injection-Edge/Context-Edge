# Main entry point for edge device

from .vision_engine import VisionEngine
from .qr_decoder import QRDecoder
from .context_injector import ContextInjectionModule
from .ldo_generator import LDOGenerator
from .opcua_protocol import OPCUAProtocol
from .modbus_protocol import ModbusProtocol
from .ethernetip_protocol import EtherNetIPProtocol
from .profinet_protocol import PROFINETProtocol
from .modbus_rtu_protocol import ModbusRTUProtocol
import time
import os
import json

def main():
    # Configuration
    context_service_url = os.getenv("CONTEXT_SERVICE_URL", "http://localhost:8000")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    protocol_type = os.getenv("PROTOCOL_TYPE", "mock")  # mock, opcua, modbus, ethernetip, profinet, modbus_rtu

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

    elif protocol_type == "ethernetip":
        ethernetip_host = os.getenv("ETHERNETIP_HOST", "192.168.1.10")
        ethernetip_port = int(os.getenv("ETHERNETIP_PORT", "44818"))
        tag_mappings = json.loads(os.getenv("ETHERNETIP_TAG_MAPPINGS", '''{
            "temperature": "Motor1_Temp",
            "vibration": "Motor1_VibrationX",
            "current": "Motor1_Current"
        }'''))
        data_protocol = EtherNetIPProtocol(ethernetip_host, tag_mappings, port=ethernetip_port)

    elif protocol_type == "profinet":
        profinet_host = os.getenv("PROFINET_HOST", "192.168.1.10")
        profinet_rack = int(os.getenv("PROFINET_RACK", "0"))
        profinet_slot = int(os.getenv("PROFINET_SLOT", "1"))
        db_mappings = json.loads(os.getenv("PROFINET_DB_MAPPINGS", '''{
            "temperature": {"db_number": 1, "start": 0, "type": "real"},
            "vibration": {"db_number": 1, "start": 4, "type": "real"},
            "pressure": {"db_number": 1, "start": 8, "type": "real"}
        }'''))
        data_protocol = PROFINETProtocol(profinet_host, rack=profinet_rack, slot=profinet_slot, db_mappings=db_mappings)

    elif protocol_type == "modbus_rtu":
        modbus_port = os.getenv("MODBUS_RTU_PORT", "/dev/ttyUSB0")
        modbus_slave_id = int(os.getenv("MODBUS_RTU_SLAVE_ID", "1"))
        modbus_baudrate = int(os.getenv("MODBUS_RTU_BAUDRATE", "9600"))
        register_mappings = json.loads(os.getenv("MODBUS_RTU_REGISTER_MAPPINGS", '''{
            "temperature": {"address": 0, "type": "holding", "count": 1, "scale": 10.0},
            "pressure": {"address": 2, "type": "holding", "count": 1, "scale": 100.0},
            "vibration": {"address": 4, "type": "holding", "count": 1, "scale": 100.0}
        }'''))
        data_protocol = ModbusRTUProtocol(
            port=modbus_port,
            register_mappings=register_mappings,
            slave_id=modbus_slave_id,
            baudrate=modbus_baudrate
        )

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