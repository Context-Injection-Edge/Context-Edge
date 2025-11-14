#!/usr/bin/env python3
"""
Demo data population script for Context Edge
Run this after starting the services with docker-compose
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def populate_demo_data():
    demo_payloads = [
        {
            "cid": "QR001",
            "metadata": {
                "product_name": "Widget A",
                "batch_number": "BATCH001",
                "pressure_threshold": 50.5,
                "temperature_range": {"min": 20, "max": 30},
                "defect_criteria": ["crack", "discoloration"]
            }
        },
        {
            "cid": "QR002",
            "metadata": {
                "product_name": "Widget B",
                "batch_number": "BATCH002",
                "pressure_threshold": 45.0,
                "temperature_range": {"min": 18, "max": 28},
                "defect_criteria": ["scratch", "bend"]
            }
        },
        {
            "cid": "QR003",
            "metadata": {
                "product_name": "Widget C",
                "batch_number": "BATCH003",
                "pressure_threshold": 55.0,
                "temperature_range": {"min": 22, "max": 32},
                "defect_criteria": ["hole", "rust"]
            }
        }
    ]

    print("Populating demo data...")

    for payload in demo_payloads:
        try:
            response = requests.post(f"{API_BASE}/context", json=payload)
            if response.status_code == 200:
                print(f"✓ Created payload for CID: {payload['cid']}")
            else:
                print(f"✗ Failed to create payload for CID: {payload['cid']} - {response.text}")
        except requests.RequestException as e:
            print(f"✗ Error connecting to API: {e}")
            print("Make sure the Context Service is running with: cd context-edge && docker-compose up")
            return

        time.sleep(0.1)  # Small delay between requests

    print("\nDemo data populated successfully!")
    print("You can now:")
    print("1. Visit the admin panel: http://localhost:3000/admin")
    print("2. View API docs: http://localhost:8000/docs")
    print("3. Test the edge SDK with the demo data")

if __name__ == "__main__":
    populate_demo_data()