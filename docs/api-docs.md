# Context Edge API Documentation

## Context Service API

Base URL: `http://localhost:8000`

### Endpoints

#### GET /context/{cid}
Retrieve metadata payload by Context ID.

**Response:**
```json
{
  "cid": "QR12345",
  "metadata": {
    "product_name": "Widget A",
    "batch_number": "BATCH001",
    "pressure_threshold": 50.5
  },
  "timestamp": "2023-11-14T12:00:00Z"
}
```

#### POST /context
Create new metadata payload.

**Request:**
```json
{
  "cid": "QR12345",
  "metadata": {
    "product_name": "Widget A",
    "batch_number": "BATCH001"
  }
}
```

#### PUT /context/{cid}
Update existing metadata payload.

#### DELETE /context/{cid}
Remove metadata payload.

## Data Ingestion API

Base URL: `http://localhost:8001`

### POST /ingest/ldo
Upload Labeled Data Object.

**Request:** Multipart form with video file and JSON metadata.

**Response:**
```json
{
  "id": "ldo_123",
  "status": "processing"
}
```

### GET /ingest/status/{id}
Check ingestion status.