FROM python:3.11-slim

WORKDIR /app

# Create storage directory
RUN mkdir -p /app/storage/ldos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy main.py directly (skip __init__.py to avoid package issues)
COPY src/main.py ./main.py

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]