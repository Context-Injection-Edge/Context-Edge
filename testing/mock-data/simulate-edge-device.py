#!/usr/bin/env python3
"""
CONTEXT EDGE - Edge Device Simulator
=====================================
⚠️  SIMULATES MOCK EDGE DEVICE FOR TESTING

Simulates a live edge device sending real-time sensor data and predictions
to the Context Edge APIs. Useful for testing real-time dashboards and
monitoring features.

Usage:
    python3 simulate-edge-device.py --device MOCK-CIM-Line1-Station1 --interval 5
"""

import argparse
import json
import random
import requests
import time
from datetime import datetime
from typing import Dict, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8000"
DATA_INGESTION_URL = "http://localhost:8001"

PRODUCTS = {
    "MOCK-WIDGET-A": 0.02,  # 2% defect rate
    "MOCK-WIDGET-B": 0.01,  # 1% defect rate
    "MOCK-WIDGET-C": 0.05,  # 5% defect rate
}


# ============================================================================
# SENSOR DATA SIMULATION
# ============================================================================

def generate_sensor_reading(is_defective: bool) -> Dict[str, float]:
    """Generate realistic sensor reading."""

    temperature = random.gauss(72.0, 8.0)
    vibration = random.gauss(2.5, 0.8)
    pressure = random.gauss(100.0, 5.0)
    humidity = random.gauss(45.0, 10.0)
    cycle_time = random.gauss(20.0, 3.0)

    # Introduce anomalies for defects
    if is_defective:
        anomaly = random.choice(["temp", "vib", "pressure"])
        if anomaly == "temp":
            temperature += random.uniform(20, 30)
        elif anomaly == "vib":
            vibration += random.uniform(4, 7)
        elif anomaly == "pressure":
            pressure += random.uniform(-25, -15) if random.random() > 0.5 else random.uniform(20, 35)

    return {
        "temperature": round(max(20, min(110, temperature)), 2),
        "vibration": round(max(0, min(15, vibration)), 2),
        "pressure": round(max(50, min(150, pressure)), 2),
        "humidity": round(max(20, min(80, humidity)), 2),
        "cycle_time": round(max(10, min(40, cycle_time)), 2),
    }


def simulate_ai_prediction(sensor_data: Dict[str, float], is_defective: bool) -> Dict[str, Any]:
    """Simulate AI model making a prediction."""

    # Model has 94% accuracy (v0.2-MOCK)
    if is_defective:
        prediction = "defective" if random.random() < 0.94 else "good"
        confidence = random.uniform(0.75, 0.98) if prediction == "defective" else random.uniform(0.40, 0.65)
    else:
        prediction = "good" if random.random() < 0.96 else "defective"
        confidence = random.uniform(0.85, 0.99) if prediction == "good" else random.uniform(0.50, 0.70)

    return {
        "model_version": "v0.2-MOCK",
        "result": prediction,
        "confidence": round(confidence, 4),
        "inference_time_ms": random.randint(15, 45),  # Realistic inference time
    }


# ============================================================================
# DEVICE SIMULATION
# ============================================================================

class MockEdgeDevice:
    """Simulates an edge device sending data to Context Edge."""

    def __init__(self, device_id: str, interval: int = 5):
        self.device_id = device_id
        self.interval = interval
        self.ldo_counter = 0
        self.total_sent = 0
        self.successful = 0
        self.failed = 0

        print(f"🤖 Initializing mock edge device: {device_id}")
        print(f"⏱️  Sending data every {interval} seconds")
        print()

    def generate_production_cycle(self) -> Dict[str, Any]:
        """Simulate one production cycle."""

        self.ldo_counter += 1

        # Random product
        product_id = random.choice(list(PRODUCTS.keys()))
        defect_rate = PRODUCTS[product_id]
        is_defective = random.random() < defect_rate

        # Generate QR code context (what operator scans)
        context = {
            "product_id": product_id,
            "line": "Line-1" if "Line1" in self.device_id else "Line-2",
            "station": self.device_id.split("-")[-1],
            "shift": self._get_current_shift(),
            "operator_id": f"OP-{random.randint(100, 199)}",
            "batch_id": f"BATCH-{datetime.now().strftime('%Y%m%d')}-{random.randint(1, 10):02d}",
        }

        # Read sensors
        sensor_data = generate_sensor_reading(is_defective)

        # AI model prediction
        prediction = simulate_ai_prediction(sensor_data, is_defective)

        # Create LDO
        ldo_id = f"MOCK-LDO-{datetime.now().strftime('%Y%m%d')}-{self.ldo_counter:06d}"

        return {
            "ldo_id": ldo_id,
            "cid": f"CID-{ldo_id}",
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "sensor_data": sensor_data,
            "prediction": prediction,
            "ground_truth": "defective" if is_defective else "good",
            "is_mock": True,
        }

    def _get_current_shift(self) -> str:
        """Determine current shift based on time."""
        hour = datetime.now().hour
        if 6 <= hour < 14:
            return "morning"
        elif 14 <= hour < 22:
            return "afternoon"
        else:
            return "night"

    def send_to_api(self, ldo: Dict[str, Any]) -> bool:
        """Send LDO to Context Edge API."""
        try:
            # Send to data ingestion endpoint
            response = requests.post(
                f"{DATA_INGESTION_URL}/ldo",
                json=ldo,
                timeout=5
            )

            if response.status_code == 200:
                return True
            else:
                print(f"❌ API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False

    def run(self):
        """Run the device simulation loop."""

        print("=" * 70)
        print(f"🏭 Starting production simulation for {self.device_id}")
        print("=" * 70)
        print()
        print("Press Ctrl+C to stop...")
        print()

        try:
            while True:
                # Generate production cycle
                ldo = self.generate_production_cycle()

                # Display info
                status_icon = "🔴" if ldo["ground_truth"] == "defective" else "🟢"
                prediction_icon = "✅" if ldo["prediction"]["result"] == ldo["ground_truth"] else "❌"

                print(f"{status_icon} LDO #{self.ldo_counter}: {ldo['ldo_id']}")
                print(f"   Product: {ldo['context']['product_id']}")
                print(f"   Sensors: T={ldo['sensor_data']['temperature']}°F, V={ldo['sensor_data']['vibration']}mm/s, P={ldo['sensor_data']['pressure']}PSI")
                print(f"   Ground Truth: {ldo['ground_truth']}")
                print(f"   {prediction_icon} Prediction: {ldo['prediction']['result']} ({ldo['prediction']['confidence']:.2%} confidence)")

                # Send to API
                success = self.send_to_api(ldo)
                self.total_sent += 1

                if success:
                    self.successful += 1
                    print(f"   ✅ Sent to API")
                else:
                    self.failed += 1
                    print(f"   ❌ Failed to send")

                # Stats
                success_rate = (self.successful / self.total_sent * 100) if self.total_sent > 0 else 0
                print(f"   📊 Stats: {self.successful}/{self.total_sent} sent ({success_rate:.1f}%)")
                print()

                # Wait for next cycle
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print()
            print("=" * 70)
            print("⏹️  Simulation stopped")
            print("=" * 70)
            print()
            print(f"📊 Final Statistics:")
            print(f"   Total LDOs: {self.total_sent}")
            print(f"   Successful: {self.successful}")
            print(f"   Failed: {self.failed}")
            print(f"   Success Rate: {(self.successful / self.total_sent * 100):.1f}%")
            print()


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Simulate edge device sending data")
    parser.add_argument("--device", type=str, default="MOCK-CIM-Line1-Station1",
                        help="Device ID to simulate")
    parser.add_argument("--interval", type=int, default=5,
                        help="Seconds between production cycles")
    args = parser.parse_args()

    # Create and run simulator
    device = MockEdgeDevice(args.device, args.interval)
    device.run()


if __name__ == "__main__":
    main()
