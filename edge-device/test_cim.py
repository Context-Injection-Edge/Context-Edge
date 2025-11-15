#!/usr/bin/env python3
"""
Simple test script for Context Injection Module (CIM)
"""

import json
import sys
from datetime import datetime

try:
    from context_edge.context_injector import ContextInjectionModule
    print("✓ Context Injection Module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Context Injection Module: {e}")
    print("\nPlease run: ./install.sh")
    sys.exit(1)

def test_cim():
    print("\n" + "="*50)
    print("Testing Context Injection Module (CIM)")
    print("="*50)

    # Initialize CIM
    api_url = "http://localhost:8000"
    print(f"\n1. Initializing CIM with API: {api_url}")
    cim = ContextInjectionModule(api_url)
    print("✓ CIM initialized")

    # Simulate sensor data
    sensor_data = {
        "temperature": 25.0,
        "pressure": 50.0,
        "timestamp": datetime.now().isoformat()
    }
    print(f"\n2. Sensor Data:")
    print(json.dumps(sensor_data, indent=2))

    # Test context injection
    qr_code = "QR001"
    print(f"\n3. Injecting context for QR Code: {qr_code}")

    try:
        ldo = cim.inject_context(sensor_data, qr_code)
        print("✓ Context injection successful!")

        print(f"\n4. Generated Labeled Data Object (LDO):")
        print(json.dumps(ldo, indent=2))

        print("\n" + "="*50)
        print("✓ All tests passed!")
        print("="*50)

    except Exception as e:
        print(f"✗ Context injection failed: {e}")
        print("\nMake sure the Context Service is running:")
        print("  cd .. && ./start.sh")
        sys.exit(1)

if __name__ == "__main__":
    test_cim()
