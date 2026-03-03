# Usage & API

## Web Interface

Start the API server and navigate to `http://127.0.0.1:5000` in your browser.
A simple form lets you submit questions and view formatted responses with
citations and confidence.

## REST Endpoints

* `GET /health` – basic uptime check
* `GET /status` – detailed status (vector store init, host/port, errors)
* `GET /examples` – returns a list of sample questions
* `POST /query` – submit a JSON body `{ "question": "..." }` and receive
  structured output including retrieved documents, generated draft, final
  answer, and metadata.

### Example cURL

```bash
curl -X POST http://127.0.0.1:5000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the notice period in Germany?"}'
```

## CLI Scenarios

`src/main.py` runs five hard‑coded queries and prints the pipeline outputs to
standard out.  This is primarily used for quick verification during
development.

