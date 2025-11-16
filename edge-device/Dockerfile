FROM python:3.11-slim

# Install system dependencies for OpenCV and pyzbar
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY edge_app/ ./edge_app/

# Run the edge device
CMD ["python", "-m", "edge_app.main"]
