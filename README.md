# EOR Copilot - Employment & Operations Compliance System

A LangGraph-based multi-agent system for HR/employment law compliance using vector search and safety guardrails.

## 🚀 Quick Start

### **Option 1: Docker (Recommended)**
```bash
docker-compose up --build
```
Runs 5 test scenarios with results displayed.

### **Option 2: Web UI**
```bash
# Terminal 1: Start Docker
docker-compose up --build

# Terminal 2: Start API
source .venv/bin/activate
python api_server.py

# Browser: http://127.0.0.1:5000
```

### **Option 3: Local**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

---

## 📋 What It Does

- ✅ Vector search for employment law policies (Qdrant + HuggingFace embeddings)
- ✅ Country-based filtering when specified in queries
- ✅ Missing variable detection (prompts for tenure, jurisdiction, etc.)
- ✅ High-risk detection (pregnancy, discrimination, harassment)
- ✅ Safety guardrails with confidence levels and escalations
- ✅ Multi-agent pipeline: Supervisor → Retriever → Generator → Critic

---

## 🏗️ Architecture

```
Query → Supervisor (intent + validation) → Retriever (vector search)
   ↓→ Generator (synthesize) → Critic (verify + escalate) → Response
```

**Agents**:
- **Supervisor**: Detects missing variables, high-risk keywords
- **Retriever**: Vector search with country filtering
- **Generator**: LLM-based response from documents
- **Critic**: Confidence scoring, escalation flags

---

## 📁 Project Structure

```
eor_copilot/
├── src/
│   ├── main.py              # Entry point (5 test scenarios)
│   ├── config.py            # Configuration
│   ├── database.py          # Qdrant setup
│   ├── graph.py             # LangGraph orchestration
│   ├── schemas.py           # Pydantic models
│   └── agents/
│       ├── supervisor.py    # Intent detection
│       ├── retriever.py     # Vector search + filtering
│       ├── generator.py     # LLM response
│       └── critic.py        # Safety & escalation
├── data/policies/
│   └── sample_policies.json # Knowledge base (14 policies)
├── api_server.py            # Flask REST API
├── query_interface.html      # Web UI
├── Dockerfile               # Container definition
├── docker-compose.yml       # Orchestration
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
└── README.md               # This file
```

---

## 🔧 Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env
OPENAI_API_KEY=sk-xxx...
QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333
```

Docker automatically installs dependencies via Dockerfile.

---

## 🌐 Web Interface

Visit `http://127.0.0.1:5000` after starting API server:
- Beautiful form to ask questions
- 6 example questions ready to click
- Formatted responses with documents & confidence
- Escalation warnings

---

## 📡 REST API

```bash
# Health check
curl http://127.0.0.1:5000/health

# Submit query
curl -X POST http://127.0.0.1:5000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is notice period in Germany?"}'
```

---

## 🧪 Test Scenarios

Running `docker-compose up --build` executes 5 scenarios:

1. **Onboarding** (Poland) - Vector search
2. **Probation** (Germany) - Retrieval
3. **Notice Period** (France) - Missing variable detection
4. **Pregnant Employee** (Germany) - High-risk escalation
5. **Multi-Country Transfer** (Germany→Austria) - Country context

---

## 📊 Knowledge Base

14 HR/employment law policies:
- **Countries**: Poland, Germany, France, UK, Spain, Italy, Portugal
- **Topics**: Probation, notice, termination, holidays, pregnancy protection
- **Format**: JSON with metadata (country, doc_id, section, timestamps)

---

## 🔑 Key Features

### Country Filtering
```
"What is notice period in Germany?"
→ Retrieves only Germany-flagged documents
```

### Missing Variables
```
"What's notice period in France?"
→ "How long has employee been with company?"
```

### High-Risk Detection
```
"Can we terminate pregnant employee?"
→ "🚨 CRITICAL ESCALATION: Pregnancy-related matter"
```

### Safety Guardrails
```
Confidence: Low/Medium/High
Escalation: Legal review needed?
Citations: Yes/No
```

---

## 📦 Tech Stack

- **Orchestration**: LangGraph, LangChain
- **Vector DB**: Qdrant (local Docker)
- **Embeddings**: HuggingFace all-MiniLM-L6-v2 (local)
- **LLM**: OpenAI gpt-3.5-turbo
- **API**: Flask
- **Validation**: Pydantic

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module flask" | `pip install -r requirements.txt` |
| "Connection refused 6333" | `docker-compose up --build` |
| "Cannot GET /" | Ensure `python api_server.py` is running |
| "OPENAI_API_KEY not found" | Create `.env` with your API key |

---

## ✅ Verification

```bash
python -c "import flask, langchain, qdrant_client; print('✅ Ready')"
```

---

## 📝 Example Queries

- "What are onboarding requirements in Poland?"
- "Can I terminate during probation in Germany?"
- "Notice period in France for 2-year employee?"
- "Can we terminate a pregnant employee?"
- "Transfer rules Germany to Austria?"

---

## 🚀 Next Steps

1. Set `OPENAI_API_KEY` in `.env`
2. Run `docker-compose up --build`
3. Visit `http://127.0.0.1:5000`
4. Ask questions!

---

**Internal use only. Do not distribute without permission.**

Infrastructure: Docker & Docker Compose.

# 🛡️ Security & Privacy (PII)
Handling HR data requires strict adherence to GDPR and internal security policies:

Zero-Retention Local Embeddings: By utilizing local HuggingFace models for our Qdrant vector store, proprietary legal frameworks remain within the secure VPC.

PII Redaction Engine (Concept): Designed to integrate with Microsoft Presidio at the gateway layer, ensuring names and SSNs are converted to secure tokens (e.g., <PERSON_1>) before ever reaching OpenAI.

Traceability: Every execution step is mapped to a state graph, allowing full auditability of why the AI generated a specific answer.

# 🚀 Getting Started
Prerequisites
* (https://docs.docker.com/get-docker/) & Docker Compose
* Git
* An OpenAI API Key

## 1. Installation
Clone the repository to your local machine:bash
git clone https://github.com/<your-username>/eor_copilot.git
cd eor_copilot


## 2. Configuration
Securely configure your environment variables. 
*(Note: The `.env` file is deliberately ignored by git for security purposes).*
```bash
cp .env.example .env

Open the .env file and insert your OpenAI API key:

Code snippet
OPENAI_API_KEY=sk-your-actual-api-key-here
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

## 3. Execution
Spin up the entire infrastructure (Qdrant Vector DB + Python Application) using Docker Compose. The build process will automatically download the local embedding models and seed the mock database.

```bash
docker-compose up --build
```

### 4. Running the test suite
A lightweight pytest-based suite verifies core logic and ensures the graph behaves as expected without needing external services. To run:

```bash
# install dependencies first (see requirements above)
pytest -q
```

Adjust or extend tests as you add functionality.

### 5. Troubleshooting
* **Qdrant connectivity** – when launching `src/main.py` from your host shell, set `QDRANT_HOST` to `localhost` (the default `.env` value `qdrant` only resolves inside Docker). Example:
  ```bash
  QDRANT_HOST=localhost python -m src.main
  ```

* **Client attribute errors** – older/newer `qdrant-client` versions may expose `query` instead of `search`. The code contains a compatibility shim, but if you encounter:
  ```text
  'QdrantClient' object has no attribute 'search'
  ```
  update your `qdrant-client` version or rely on the shim in `src/database.py`.

* **Signature mismatches** – the retriever now calls `get_relevant_documents()` explicitly to avoid the `QdrantFastembedMixin.query()` error where an unexpected `query_text` argument was required. If you still see complaints, upgrade `langchain-community` or adjust the call appropriately.

* **NumPy/pytorch issues** – local conda environments often trigger
  `numpy.dtype size changed` errors when mixing package versions. Use a fresh venv and install requirements, or downgrade numpy to `<2.0`.

* **Offline / missing Qdrant** – when the vector database is unreachable or
  qdrant-client fails to initialize (e.g. during fast unit testing), the
  retriever automatically falls back to a simple keyword scan of the bundled
  `data/policies/sample_policies.json` file. The database is seeded with the
  same three documents at first start, so you can run the demo questions even
  without an active vector store. Paths are resolved from the project root so
  the search should always succeed when the sample data exists. If you see an
  empty result set, make sure the file is present and that your query matches
  its contents.

* **Warning message during retrieval** – if you encounter the log:
  ```text
  Retriever warning: no compatible retrieval method found (checked [...],
  available []), falling back to keyword scan
  ```
  this is not a fatal error. It simply means the object returned by
  `vector_store.as_retriever()` didn't expose any of the expected APIs (e.g.
  `search`, `get_relevant_documents`) for the current LangChain/vectorstore
  version. The code will automatically perform a local keyword search instead
  of semantic ranking. To debug further, the warning includes the first few
  non‑dunder methods on the retriever so you can verify what interface it
  actually implements. If you consistently see this message while Qdrant is
  running, consider upgrading `langchain`, `langchain-community`, or
  inspecting your vector‑store wrapper; otherwise it's safe to ignore.

Feel free to open an issue if you hit something not covered above.


🧪 Demo Scenarios
Upon running, the application will automatically execute src/main.py, demonstrating the following edge cases:

Standard Retrieval (High Confidence): Queries standard German probation laws or French notice‑period rules (we seed the database with three sample documents – Poland onboarding, Germany probation and France notice period) and successfully returns the exact text.

Missing Variables (Cost-Saving Halt): Asks about French notice periods without providing tenure. The Supervisor intercepts the request and asks a follow-up question before triggering the LLM.

High-Risk Escalation (Safety Guardrail): Simulates an HR request to terminate a pregnant employee in Spain. The Critic Agent identifies the protected class, degrades confidence to "Low", and issues an urgent escalation to consult Legal Counsel.

```
📂 Project Structure
eor_copilot/
├── docker-compose.yml       # Infrastructure orchestration
├── Dockerfile               # Python environment setup
├── requirements.txt         # Dependencies
├──.env.example              # Template for secrets
├── src/
│   ├── main.py              # Application entry point & demo runner
│   ├── config.py            # Environment variable management
│   ├── schemas.py           # Pydantic data models for structured output
│   ├── database.py          # Qdrant initialization and local embeddings
│   ├── graph.py             # LangGraph state machine definition
│   └── agents/
│       ├── supervisor.py    # Intent routing and parameter checking
│       ├── retriever.py     # Qdrant semantic search
│       ├── generator.py     # Draft synthesis
│       └── critic.py        # Compliance validation and escalation
```