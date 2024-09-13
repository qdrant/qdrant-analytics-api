# Qdrant Analytics API
### Scope
This service manages analytics from all sources of interest: Marketing Site, Cloud UI, Cluster API and delivers these events to Segment for downstream processing.

## Local Development
### Running
Start virtual environment
```
source env/bin/activate
```
Install dependencies
```
pip install -r requirements.txt
```

Start the server with
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Environment Variables (.env)

```
APP_TZ=UTC
API_AUTHENTICATION_KEY=...
SEGMENT_WRITE_KEY=...
ALLOWED_ORIGINS=http://localhost:1313,http://localhost:3000
```

### Testing
Run from the root directory
```
PYTHONPATH=. pytest app/tests
```

## Using API

### Endpoints
Requires authentication token (`API_AUTHENTICATION_KEY`) and allow listing origin(s) (`ALLOWED_ORIGINS`)
- /healthcheck (GET request)
- /anonymous_id (GET request)
- /identify (POST request)
- /track (POST request)
- /page (POST request)

### Locally
Make requests to http://0.0.0.0:8000

## Segment Environments
- Development
- Staging
- Production

### Segment Debuggers
- [Development Debugger Dashboard](https://app.segment.com/qdrant-dev/sources/server_side_tracking/debugger)
- [Staging Debugger Dashboard](https://app.segment.com/qdrant-staging/sources/server_side_tracking/debugger) (to be setup)
- [Production Debugger Dashboard](https://app.segment.com/qdrant-production/sources/server_side_tracking/debugger) (to be setup)
