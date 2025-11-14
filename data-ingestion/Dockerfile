FROM python:3.11-slim

WORKDIR /app

# Create storage directory
RUN mkdir -p /app/storage/ldos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]