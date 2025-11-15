# Dashboard Enhancements for Industrial RAG

## MER Report Features

Add to the admin panel (`context-edge-ui/src/app/admin/`):

### MER Report Page (`/admin/mer-reports`)
- List of Maintenance Event Records with:
  - Asset ID, Time/Date, Predicted Failure Mode, AI Confidence Score
  - Video clip player (5-10 second snippet)
  - Sensor timeline chart (vibration, temp, current for 60s before/after event)
  - PLC/state snapshot at event time
- Validation controls:
  - "Confirm Issue" button (saves for retraining)
  - "False Alarm" button (flags for exclusion)
  - "Work Order Created" link to CMMS ticket
  - Notes field for corrective action details

## Threshold Management UI

### Threshold Editor Page (`/admin/thresholds`)
- Visual interface for sensor limits:
  - Graphical sliders for Warning/Critical thresholds
  - Real-time preview of threshold ranges
  - Save to Redis Context Store via API

### Asset Configuration Page (`/admin/assets`)
- Link physical asset IDs to sensor tags
- Store asset master data (location, model, safety rules)

## MLOps Interface

### Model Management Page (`/admin/models`)
- List of available AI model versions
- Current model status on edge devices
- Deploy button to push new models via Kubernetes

### Feedback Queue Page (`/admin/feedback`)
- Low-confidence predictions waiting for validation
- Batch processing for retraining data

## API Integration

Update frontend to call new Context Service APIs:
- `/context/assets` - Asset management
- `/context/thresholds` - Threshold configuration
- `/context/runtime` - Runtime state updates
- `/context/models` - Model metadata
- `/feedback/low-confidence` - Submit feedback

## Implementation Notes

- Build on existing Next.js/React structure
- Use existing UI components and styling
- Add new API client functions
- Implement real-time updates for MER alerts