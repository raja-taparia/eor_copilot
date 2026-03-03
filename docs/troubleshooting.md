# Troubleshooting

This file collects common issues, diagnostics, and debugging commands.

## OpenAI API Key

* **Error**: `Incorrect API key provided` or 401 responses.
  * Ensure `.env` contains the correct key and `OPENAI_API_KEY` is not
    exported to a different (old) value.  Run `unset OPENAI_API_KEY` if
    necessary.
  * `api_server.py` prints a truncated key at startup for verification.

## Qdrant Connectivity

* When the API server runs outside Docker, `QDRANT_HOST` must be
  `localhost` or `127.0.0.1` (the service name `qdrant` only works inside the
  compose network).  The configuration automatically rewrites this value but
  you may also set it manually.
* **Error**: `Cannot reach Qdrant at qdrant:6333: [Errno 8]` indicates an
  incorrect host.
* Use `python test_qdrant_connection.py` to run a diagnostic suite. It will
  report the effective host/port, connectivity, embedding load, and API
  routes.

## Dependencies

* Missing modules (e.g. `flask`, `langchain_openai`) → `pip install -r requirements.txt`.
* If embedding model fails load, ensure `torch` and `numpy` are installed.

## Docker

* Qdrant container may take several seconds to become healthy; wait before
  querying.
* To rebuild with updated code: `docker-compose up --build`.

## Logging

* The API server prints initialization status and errors to the console.
* You can call `/status` or `/health` endpoints for runtime information.

