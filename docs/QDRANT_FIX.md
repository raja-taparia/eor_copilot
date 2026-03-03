# 🔧 Fixing Qdrant Connectivity Issue

Your `api_server.py` was unable to connect to Qdrant because there was no connection testing or retry logic on initialization. I've now added comprehensive error handling and diagnostics.

## What Changed

### 1. **api_server.py** - Enhanced Initialization
- ✅ Added `test_qdrant_connection()` function with retries (5 attempts with 2-second delays)
- ✅ Calls `initialize_vector_store()` on **startup** (not on first request)
- ✅ Added `/health` and `/status` endpoints to check Qdrant status
- ✅ Updated `/query` endpoint to verify vector store before processing
- ✅ Better error messages with troubleshooting hints

### 2. **src/database.py** - Connection Verification
- ✅ Added timeout (5 seconds) to Qdrant client initialization
- ✅ Test connection by calling `get_collections()` before using it
- ✅ Check if collection has data and re-seed if empty
- ✅ Better logging at each initialization step

### 3. **test_qdrant_connection.py** - New Diagnostic Tool
- Tests basic Qdrant connectivity
- Tests HuggingFace embeddings model
- Tests full vector store initialization
- Tests API server routes
- Provides troubleshooting hints

---

## 🚀 How to Fix the Issue

### Step 1: Start Qdrant (in Terminal 1)
```bash
docker-compose up --build
```

**Wait for the output to show:**
```
✅ Qdrant is running at http://127.0.0.1:6333
```

### Step 2: Test Qdrant Connection (in Terminal 2)
```bash
python test_qdrant_connection.py
```

This will run diagnostics and show:
- ✅ Basic Qdrant connectivity
- ✅ Embeddings model status  
- ✅ Vector store initialization
- ✅ API server route accessibility

### Step 3: Start API Server (in Terminal 2 or 3)
```bash
python api_server.py
```

You should see:
```
🔍 Testing Qdrant connection at 127.0.0.1:6333...
✅ Qdrant is reachable! Collections: 1

🔄 Initializing vector store...
   ✅ Connected to Qdrant. Found 1 existing collection(s)
   ✅ Collection 'eor_policies' exists with 60 documents
   ✅ Vector store initialized successfully

╔════════════════════════════════════════════════════════════════╗
║  USAGE:                                                        ║
║  • Web Interface: http://127.0.0.1:5000                        ║
║  • Health check: curl http://127.0.0.1:5000/health             ║
║  • Status check: curl http://127.0.0.1:5000/status             ║
...
```

### Step 4: Access the Web Interface
Open browser to: **http://127.0.0.1:5000**

Fill out the form and ask a question. It should now work!

---

## 🔍 Troubleshooting

### Issue: "Cannot reach Qdrant at 127.0.0.1:6333"
**Solution:**
1. Check if Qdrant is running: `docker ps`
2. Restart Qdrant: `docker-compose down && docker-compose up --build`
3. Wait 5-10 seconds for Qdrant to be fully ready

### Issue: "Vector store not available" on API
**Solution:**
1. Run `python test_qdrant_connection.py` to identify exact failure
2. Check if embeddings model can load (requires torch/numpy)
3. Check if sample_policies.json exists in `data/policies/`

### Issue: API responds with 503 when submitting query
**Solution:**
- Your vector store initialization failed
- Check the error message in `/status` endpoint:
  ```bash
  curl http://127.0.0.1:5000/status
  ```
- Fix the reported error (usually Qdrant not running or data not seeded)

---

## ✅ Quick Health Check Commands

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Check API server health
curl http://127.0.0.1:5000/health

# Check API server status with details
curl http://127.0.0.1:5000/status

# List example queries
curl http://127.0.0.1:5000/examples

# Submit a test query
curl -X POST http://127.0.0.1:5000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the notice period in Germany?"}'
```

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────┐
│   Your Computer (Host Machine)       │
├─────────────────────────────────────┤
│                                      │
│  ┌──────────────────────────────┐   │
│  │   api_server.py (Flask)       │   │
│  │   Port: 5000                   │   │
│  │                                │   │
│  │  /health    - Check status     │   │
│  │  /status    - Detailed info    │   │
│  │  /query     - Process questions│   │
│  │  /examples  - Example queries  │   │
│  └────────────┬───────────────────┘   │
│               │                        │
│               │ connect to             │
│               │ 127.0.0.1:6333         │
│               │                        │
│              ▼                         │
│  ┌──────────────────────────────┐   │
│  │   Docker Container           │   │
│  │   Qdrant Vector Database      │   │
│  │   Port: 6333 (exposed)        │   │
│  │   Stores: eor_policies        │   │
│  │           60 document chunks  │   │
│  └──────────────────────────────┘   │
│                                      │
└─────────────────────────────────────┘
```

---

## 🎯 Next Steps

1. **Run the diagnostic tool:**
   ```bash
   python test_qdrant_connection.py
   ```

2. **Start Docker (if not already running):**
   ```bash
   docker-compose up --build
   ```

3. **Start the API server:**
   ```bash
   python api_server.py
   ```

4. **Access the web interface:**
   - Open http://127.0.0.1:5000 in your browser

5. **Test with a query:**
   - Example: "What are the notice periods in Germany?"

---

## 💡 Key Improvements Made

| Issue | Solution |
|-------|----------|
| No connection testing | Added retry logic with exponential backoff |
| Silent initialization errors | Enhanced logging at every step |
| No vector store status endpoint | Added `/health` and `/status` endpoints |
| Initialization on 1st request (slow) | Moved to server startup |
| No way to diagnose issues | Created `test_qdrant_connection.py` diagnostic tool |
| Connection timeout issues | Added explicit 5-second timeout to client |
| Empty collection issues | Check collection size and re-seed if needed |

---

Still having issues? Run this command to get detailed diagnostics:
```bash
python test_qdrant_connection.py
```

This will show exactly where the problem is and provide specific solutions! 🔍
