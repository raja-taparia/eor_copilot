# Architecture Overview

`eor_copilot` is a multi-agent system built on LangGraph/LangChain.  It
provides HR compliance answers by searching a vectorized policy database and
running a lightweight reasoning pipeline.

## Components

* **Supervisor Agent** – inspects the question for missing variables (country,
  tenure, etc.) and high-risk terms that require escalation.
* **Retriever Agent** – performs a vector similarity search against Qdrant;
  applies country filters when detected.
* **Generator Agent** – uses OpenAI (gpt-3.5-turbo) to craft a draft answer
  based solely on retrieved documents.
* **Critic Agent** – evaluates the model output for confidence and issues
  escalation flags or follow‑up prompts.

## Data Flow

```
User question
      ↓
Supervisor ──> (maybe follow-up) ──> Retriever (Qdrant search)
      ↓                                ↓
Generator (LLM) ←───────── Critic (confidence/esc)
      ↓
Final response + citations
```

## Vector Database

* **Qdrant** running in Docker (port 6333).
* Documents are seeded from `data/policies/sample_policies.json`.
* Each policy is chunked into overlapping text pieces; metadata includes
  `country`, `doc_id`, `section_id`, etc.

## Deployment

* `docker-compose.yml` brings up Qdrant alongside a one-off script that
  executes the demo scenarios.
* `api_server.py` hosts a Flask REST interface for interactive queries.

