#!/usr/bin/env python3
"""
CONTEXT EDGE - Mock LDO Generator
==================================
⚠️  GENERATES MOCK TEST DATA ONLY

Creates realistic Labeled Data Objects (LDOs) with:
- Realistic sensor readings (temperature, vibration, pressure)
- Product context from QR codes
- Timestamp distribution over 30 days
- Mix of good/defective parts
- Predictions from AI models
- Feedback queue items

All data is marked with is_mock = true and MOCK- prefixes.
"""

import argparse
import json
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8000"
DATA_INGESTION_URL = "http://localhost:8001"

# Mock products with different defect rates
PRODUCTS = {
    "MOCK-WIDGET-A": {"defect_rate": 0.02, "description": "Standard widget"},
    "MOCK-WIDGET-B": {"defect_rate": 0.01, "description": "Premium widget"},
    "MOCK-WIDGET-C": {"defect_rate": 0.05, "description": "Economy widget"},
}

# Mock edge devices
DEVICES = [
    "MOCK-CIM-Line1-Station1",
    "MOCK-CIM-Line1-Station2",
    "MOCK-CIM-Line2-Station1",
    "MOCK-CIM-Line2-Station2",
]

# Defect types with probabilities
DEFECT_TYPES = [
    ("surface_crack", 0.30),
    ("scratch", 0.25),
    ("misalignment", 0.20),
    ("contamination", 0.15),
    ("dimensional_error", 0.10),
]

# Shifts
SHIFTS = {
    "morning": {"start": 6, "end": 14, "quality": 0.95},
    "afternoon": {"start": 14, "end": 22, "quality": 0.93},
    "night": {"start": 22, "end": 6, "quality": 0.90},  # Slightly lower quality
}


# ============================================================================
# SENSOR DATA GENERATION
# ============================================================================

def generate_sensor_data(product_id: str, is_defective: bool) -> Dict[str, float]:
    """Generate realistic sensor data with anomalies for defects."""

    # Base sensor readings
    temperature = random.gauss(72.0, 8.0)  # °F, mean 72, stddev 8
    vibration = random.gauss(2.5, 0.8)  # mm/s, mean 2.5, stddev 0.8
    pressure = random.gauss(100.0, 5.0)  # PSI, mean 100, stddev 5
    humidity = random.gauss(45.0, 10.0)  # %, mean 45, stddev 10
    cycle_time = random.gauss(20.0, 3.0)  # seconds

    # Introduce anomalies for defective parts
    if is_defective:
        anomaly_type = random.choice(["temp", "vib", "pressure", "time"])
        if anomaly_type == "temp":
            temperature += random.uniform(15, 25)  # Overheating
        elif anomaly_type == "vib":
            vibration += random.uniform(3, 6)  # Excessive vibration
        elif anomaly_type == "pressure":
            pressure += random.uniform(-20, -10) if random.random() > 0.5 else random.uniform(15, 30)
        elif anomaly_type == "time":
            cycle_time += random.uniform(5, 10)  # Slow cycle

    # Clamp to reasonable ranges
    temperature = max(20, min(110, temperature))
    vibration = max(0, min(15, vibration))
    pressure = max(50, min(150, pressure))
    humidity = max(20, min(80, humidity))
    cycle_time = max(10, min(40, cycle_time))

    return {
        "temperature": round(temperature, 2),
        "vibration": round(vibration, 2),
        "pressure": round(pressure, 2),
        "humidity": round(humidity, 2),
        "cycle_time": round(cycle_time, 2),
    }


def get_shift(hour: int) -> str:
    """Determine shift based on hour."""
    if 6 <= hour < 14:
        return "morning"
    elif 14 <= hour < 22:
        return "afternoon"
    else:
        return "night"


def generate_timestamp(days_ago: int) -> datetime:
    """Generate random timestamp within working hours, X days ago."""
    date = datetime.now() - timedelta(days=days_ago)

    # Random hour during production (6am - 10pm, skipping night shift sometimes)
    if random.random() > 0.2:  # 80% day/afternoon shifts
        hour = random.randint(6, 21)
    else:  # 20% night shift
        hour = random.choice([22, 23, 0, 1, 2, 3, 4, 5])

    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return date.replace(hour=hour, minute=minute, second=second)


def select_defect_type() -> str:
    """Randomly select a defect type based on probabilities."""
    defects, probs = zip(*DEFECT_TYPES)
    return random.choices(defects, weights=probs)[0]


# ============================================================================
# LDO GENERATION
# ============================================================================

def generate_mock_ldo(ldo_number: int, timestamp: datetime) -> Dict[str, Any]:
    """Generate a single mock LDO."""

    # Select random product and device
    product_id = random.choice(list(PRODUCTS.keys()))
    device_id = random.choice(DEVICES)

    # Determine if defective based on product defect rate
    defect_rate = PRODUCTS[product_id]["defect_rate"]
    shift = get_shift(timestamp.hour)
    shift_quality = SHIFTS[shift]["quality"]

    # Adjust defect rate based on shift (night shift has slightly more defects)
    adjusted_defect_rate = defect_rate * (1.0 + (1.0 - shift_quality))
    is_defective = random.random() < adjusted_defect_rate

    # Generate sensor data
    sensor_data = generate_sensor_data(product_id, is_defective)

    # Create LDO ID
    ldo_id = f"MOCK-LDO-2024-{ldo_number:06d}"

    # QR code context (what the operator scans)
    context = {
        "product_id": product_id,
        "line": "Line-1" if "Line1" in device_id else "Line-2",
        "station": device_id.split("-")[-1],
        "shift": shift,
        "operator_id": f"OP-{random.randint(100, 199)}",
        "batch_id": f"BATCH-{timestamp.strftime('%Y%m%d')}-{random.randint(1, 10):02d}",
    }

    # Model prediction (using v0.2-MOCK which is "deployed")
    model_version = "v0.2-MOCK"

    # Simulate model prediction
    if is_defective:
        # Model should catch most defects, but not all (94% accuracy)
        prediction = "defective" if random.random() < 0.94 else "good"
        confidence = random.uniform(0.75, 0.98) if prediction == "defective" else random.uniform(0.40, 0.65)
    else:
        # Model correctly identifies good parts most of the time
        prediction = "good" if random.random() < 0.96 else "defective"
        confidence = random.uniform(0.85, 0.99) if prediction == "good" else random.uniform(0.50, 0.70)

    # Determine if this needs operator feedback (low confidence)
    needs_feedback = confidence < 0.70

    return {
        "ldo_id": ldo_id,
        "cid": f"CID-{ldo_id}",
        "device_id": device_id,
        "timestamp": timestamp.isoformat(),
        "context": context,
        "sensor_data": sensor_data,
        "prediction": {
            "model_version": model_version,
            "result": prediction,
            "confidence": round(confidence, 4),
        },
        "ground_truth": "defective" if is_defective else "good",
        "needs_feedback": needs_feedback,
        "is_mock": True,
    }


# ============================================================================
# DATABASE INSERTION
# ============================================================================

def insert_ldos_to_database(ldos: List[Dict[str, Any]]):
    """Insert LDOs directly into PostgreSQL database."""
    import psycopg2
    from psycopg2.extras import execute_batch

    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="context_edge",
            user="context_user",
            password="context_pass"
        )
        cur = conn.cursor()

        # Prepare data for batch insert
        ldo_data = []
        prediction_data = []
        feedback_data = []

        for ldo in ldos:
            # Insert into metadata_payloads
            payload = {
                "context": ldo["context"],
                "sensor_data": ldo["sensor_data"],
                "ground_truth": ldo["ground_truth"],
            }
            ldo_data.append((
                ldo["cid"],
                json.dumps(payload),
                ldo["timestamp"],
                ldo["timestamp"],
                True  # is_mock
            ))

            # Insert prediction
            prediction_data.append((
                ldo["ldo_id"],
                ldo["device_id"],
                ldo["prediction"]["model_version"],
                ldo["prediction"]["result"],
                ldo["prediction"]["confidence"],
                json.dumps(ldo["sensor_data"]),
                json.dumps(ldo["context"]),
                True,  # is_mock
                ldo["timestamp"]
            ))

            # Insert to feedback queue if needed
            if ldo["needs_feedback"]:
                feedback_data.append((
                    ldo["ldo_id"],
                    ldo["device_id"],
                    ldo["prediction"]["result"],
                    ldo["prediction"]["confidence"],
                    "high" if ldo["prediction"]["confidence"] < 0.60 else "normal",
                    True,  # is_mock
                    ldo["timestamp"]
                ))

        # Batch insert LDOs
        execute_batch(cur, """
            INSERT INTO metadata_payloads (cid, payload_data, created_at, updated_at, is_mock)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cid) DO NOTHING
        """, ldo_data)

        # Batch insert predictions
        execute_batch(cur, """
            INSERT INTO predictions (ldo_id, device_id, model_version, prediction, confidence, sensor_data, context_data, is_mock, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, prediction_data)

        # Batch insert feedback items
        if feedback_data:
            execute_batch(cur, """
                INSERT INTO feedback_queue (ldo_id, device_id, prediction, confidence, priority, is_mock, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, feedback_data)

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Inserted {len(ldos)} LDOs into database")
        print(f"✅ Inserted {len(prediction_data)} predictions")
        print(f"✅ Inserted {len(feedback_data)} feedback items")

    except Exception as e:
        print(f"❌ Database error: {e}")
        raise


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate mock LDOs for testing")
    parser.add_argument("--count", type=int, default=1000, help="Number of LDOs to generate")
    parser.add_argument("--days", type=int, default=30, help="Spread data over N days")
    parser.add_argument("--output", type=str, help="Output to JSON file instead of database")
    args = parser.parse_args()

    print("=" * 70)
    print("CONTEXT EDGE - Mock LDO Generator")
    print("=" * 70)
    print(f"🧪 Generating {args.count} mock LDOs over {args.days} days")
    print()

    # Generate LDOs
    ldos = []
    for i in range(1, args.count + 1):
        days_ago = random.randint(0, args.days)
        timestamp = generate_timestamp(days_ago)
        ldo = generate_mock_ldo(i, timestamp)
        ldos.append(ldo)

        if i % 100 == 0:
            print(f"  Generated {i}/{args.count} LDOs...")

    print(f"✅ Generated {len(ldos)} LDOs")
    print()

    # Output results
    if args.output:
        # Save to JSON file
        with open(args.output, "w") as f:
            json.dump(ldos, f, indent=2)
        print(f"✅ Saved to {args.output}")
    else:
        # Insert into database
        print("📊 Inserting into database...")
        insert_ldos_to_database(ldos)

    # Statistics
    defective_count = sum(1 for ldo in ldos if ldo["ground_truth"] == "defective")
    feedback_count = sum(1 for ldo in ldos if ldo["needs_feedback"])

    print()
    print("📈 Statistics:")
    print(f"  Total LDOs: {len(ldos)}")
    print(f"  Defective: {defective_count} ({defective_count/len(ldos)*100:.1f}%)")
    print(f"  Needs Feedback: {feedback_count} ({feedback_count/len(ldos)*100:.1f}%)")
    print()
    print("✅ Mock LDO generation complete!")
    print()


if __name__ == "__main__":
    main()
