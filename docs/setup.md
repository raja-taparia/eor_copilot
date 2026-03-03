# Setup & Installation

This document covers getting the project running locally or via Docker.

## Prerequisites

* Python 3.9+ (virtual environment recommended)
* Docker & docker-compose (for vector database)
* An OpenAI API key (sign up at https://platform.openai.com)

## Installing Dependencies

```bash
# create and activate venv
python -m venv .venv
source .venv/bin/activate

# install Python requirements
pip install -r requirements.txt
```

## Configuration

Copy the example file and update values:

```bash
cp .env.example .env
# then edit .env with your API key
```

Typical `.env` contents:

```dotenv
OPENAI_API_KEY=sk-...
QDRANT_HOST=127.0.0.1        # use 'qdrant' only when running inside Docker
QDRANT_PORT=6333
```

> The code automatically translates `qdrant` to `127.0.0.1` when the
> API server is executed on the host machine.

## Running

### With Docker (recommended)

```bash
docker-compose up --build
```

The container runs five demo scenarios and exposes the API on
`http://127.0.0.1:5000`.

### Locally

```bash
# start Qdrant manually
docker-compose up qdrant

python api_server.py
```

or run the standalone CLI exercise:

```bash
python src/main.py
```

