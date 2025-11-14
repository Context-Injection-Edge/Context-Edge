# Context Edge Demo Environment

This directory contains sample data and scripts to set up a demo environment for Context Edge.

## Quick Demo Setup

1. **Start the services:**
   ```bash
   cd ../
   docker-compose up -d
   ```

2. **Populate demo data:**
   ```bash
   python demo/populate_demo_data.py
   ```

3. **Start the UI:**
   ```bash
   cd ../context-edge-ui
   npm run dev
   ```

4. **Access the demo:**
   - Main site: http://localhost:3000
   - Admin panel: http://localhost:3000/admin
   - API docs: http://localhost:8000/docs

## Sample Data

The demo includes sample metadata for QR codes QR001, QR002, QR003 with manufacturing data like:
- Product names and batch numbers
- Pressure thresholds
- Temperature ranges
- Defect criteria

## Testing the Edge SDK

1. **Install the SDK:**
   ```bash
   cd ../edge-device
   pip install -e .
   ```

2. **Run a simple test:**
   ```python
   from context_edge import ContextInjectionModule

   cim = ContextInjectionModule("http://localhost:8000")
   sensor_data = {"temperature": 25.0, "pressure": 50.0}
   result = cim.inject_context(sensor_data, "QR001")
   print(result)
   ```

## Files

- `sample_metadata.csv` - Sample CSV for bulk import
- `populate_demo_data.py` - Script to populate demo data via API
- `README.md` - This file