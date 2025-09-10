# API Reference

The Optics Framework exposes a FastAPI server for programmatic control of sessions and keyword execution.

## Starting the Server

Run the server via CLI:

```bash
optics serve --host 127.0.0.1 --port 8000
```

Check health:

```http
GET /
```
Returns JSON with `status` and `version`.

## Sessions

- `POST /v1/sessions/start`
  - Body: JSON matching SessionConfig
    - `driver_sources`, `elements_sources`, `text_detection`, `image_detection`: arrays of strings or objects like `{ "appium": { "enabled": true, "url": "...", "capabilities": { ... } } }`
    - `project_path` (optional): base path for templates and API YAML
  - Response: `{ "session_id": "...", "status": "created" }`

- `DELETE /v1/sessions/{session_id}/stop`
  - Terminates the session and underlying driver.

## Keyword Execution

- `POST /v1/sessions/{session_id}/action`
  - Body: `{ "mode": "keyword", "keyword": "Press Element", "params": ["${Home_text}"] }`
  - Response: `{ "execution_id": "...", "status": "SUCCESS", "data": { "result": ... } }`

- `GET /v1/sessions/{session_id}/events`
  - Server-Sent Events stream of execution updates and heartbeats.

## Convenience Endpoints

- `GET /v1/session/{session_id}/screenshot` → `Capture Screenshot`
- `GET /v1/session/{session_id}/source` → `Capture Page Source`
- `GET /session/{session_id}/driver-id` → `Get Driver Session Id`
- `GET /v1/session/{session_id}/screen_elements` → screenshot + detected elements

Notes:
- For Appium, you can supply top-level `appium_url` and `appium_config`, but these are deprecated; prefer embedding under `driver_sources` as shown above.
- CORS is enabled for all origins to simplify local integration.
