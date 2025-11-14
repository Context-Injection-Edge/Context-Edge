FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY start.sh ./

RUN chmod +x start.sh

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["/bin/bash", "-c", "echo 'Waiting for database...' && sleep 5 && echo 'Initializing database...' && python -c 'from src.database.init_db import init_db; init_db()' && echo 'Starting service...' && exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"]