#!/usr/bin/env python3
"""
REST API for EOR Copilot
Provides HTTP endpoints for querying employment law knowledge base.
Requires Qdrant to be running (docker-compose up).
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file

# Load .env file BEFORE importing any agents that depend on OPENAI_API_KEY
# override=True ensures values from .env take precedence over exported ones
load_dotenv(override=True)

os.environ['QDRANT_HOST'] = '127.0.0.1'
os.environ['QDRANT_PORT'] = '6333'
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_core.messages import HumanMessage
from agents.supervisor import supervisor_agent
from agents.retriever import retriever_agent
from agents.generator import generator_agent
from agents.critic import critic_agent
from database import get_qdrant_vector_store

app = Flask(__name__, static_folder=Path(__file__).parent)
vector_store = None
initialization_error = None

# debug: show relevant environment values at startup (not full key)
OPENAI_CHECK = os.getenv("OPENAI_API_KEY", "<not set>")
if OPENAI_CHECK and OPENAI_CHECK != "<not set>":
    display = OPENAI_CHECK if len(OPENAI_CHECK) < 10 else f"{OPENAI_CHECK[:4]}...{OPENAI_CHECK[-4:]}"
else:
    display = OPENAI_CHECK
print(f"[startup] OPENAI_API_KEY={display}")

def test_qdrant_connection(host='127.0.0.1', port=6333, retries=5, delay=2):
    """Test Qdrant connectivity with retries"""
    from qdrant_client import QdrantClient
    
    print(f"\n🔍 Testing Qdrant connection at {host}:{port}...")
    
    for attempt in range(1, retries + 1):
        try:
            client = QdrantClient(host=host, port=port)
            # Try to get collection info
            collections = client.get_collections()
            print(f"✅ Qdrant is reachable! Collections: {len(collections.collections)}")
            return True
        except Exception as e:
            if attempt < retries:
                print(f"   ⚠️  Attempt {attempt}/{retries} failed: {str(e)[:80]}")
                print(f"   ⏳ Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"   ❌ Failed after {retries} attempts: {str(e)[:100]}")
                return False
    return False

def initialize_vector_store():
    """Initialize vector store with connection testing"""
    global vector_store, initialization_error
    
    try:
        print("\n🔄 Initializing vector store...")
        
        # Test Qdrant connection first
        if not test_qdrant_connection():
            raise ConnectionError(
                "Cannot reach Qdrant at 127.0.0.1:6333\n"
                "Make sure 'docker-compose up --build' is running in another terminal.\n"
                "Web interface will still work, but queries will fail."
            )
        
        # Initialize vector store
        vector_store = get_qdrant_vector_store()
        print("✅ Vector store initialized successfully")
        initialization_error = None
        return True
        
    except Exception as e:
        error_msg = f"Vector store initialization failed: {str(e)}"
        print(f"❌ {error_msg}")
        initialization_error = str(e)
        return False

def get_vector_store():
    """Get or initialize vector store, with error handling"""
    global vector_store
    
    if vector_store is None:
        print("⏳ Initializing vector store on first request...")
        if not initialize_vector_store():
            raise RuntimeError(initialization_error or "Vector store not available")
    
    return vector_store

@app.route('/', methods=['GET'])
def index():
    """Serve the main HTML interface"""
    html_file = Path(__file__).parent / 'query_interface.html'
    if html_file.exists():
        return send_file(html_file)
    return jsonify({"error": "Web interface not found"}), 404

@app.route('/index.html', methods=['GET'])
@app.route('/query_interface.html', methods=['GET'])
def html_interface():
    """Serve HTML interface on multiple paths"""
    html_file = Path(__file__).parent / 'query_interface.html'
    if html_file.exists():
        return send_file(html_file)
    return jsonify({"error": "Web interface not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check with Qdrant status"""
    status = {
        "status": "ok",
        "service": "EOR Copilot",
        "vector_store": "ready" if vector_store else "not_initialized"
    }
    
    if initialization_error:
        status["error"] = initialization_error
        status["status"] = "degraded"
    
    return jsonify(status), 200

@app.route('/status', methods=['GET'])
def status():
    """Detailed status information"""
    return jsonify({
        "service": "EOR Copilot API",
        "version": "1.0",
        "vector_store_initialized": vector_store is not None,
        "qdrant_host": os.getenv('QDRANT_HOST', '127.0.0.1'),
        "qdrant_port": os.getenv('QDRANT_PORT', '6333'),
        "error": initialization_error
    }), 200

@app.route('/query', methods=['POST'])
def query():
    """
    Main query endpoint
    
    Request body:
    {
        "question": "What is the notice period in Germany?"
    }
    
    Response:
    {
        "question": "...",
        "supervisor_output": {...},
        "retrieved_documents": [...],
        "draft_response": "...",
        "final_response": {...},
        "metadata": {
            "country": "Germany",
            "doc_count": 3,
            "confidence": "High"
        }
    }
    """
    try:
        # Validate request
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                "error": "Missing 'question' field in request body",
                "example": {"question": "What is the notice period in Germany?"}
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({"error": "Question cannot be empty"}), 400
        
        print(f"\n📝 Received query: {question}")
        
        # Ensure vector store is initialized (with error handling)
        try:
            store = get_vector_store()
            print(f"   ✅ Vector store ready")
        except RuntimeError as e:
            print(f"   ❌ Vector store unavailable: {e}")
            return jsonify({
                "error": "Vector database not available",
                "details": str(e),
                "hint": "Make sure 'docker-compose up --build' is running in another terminal"
            }), 503
        
        # Run through agent pipeline
        supervisor_result = supervisor_agent({"query": question})
        
        # Package response
        response_data = {
            "question": question,
            "supervisor_output": supervisor_result.get("final_output", {}),
        }
        
        # If supervisor didn't find follow-up questions needed, continue
        if not supervisor_result.get("final_output", {}).get("follow_up_questions"):
            state = {
                "query": question,
                "messages": [HumanMessage(content=question)]
            }
            
            retriever_result = retriever_agent(state)
            retrieved_docs = retriever_result.get("retrieved_docs", [])
            
            response_data["retrieved_documents"] = [
                {
                    "doc_id": doc.metadata.get("doc_id", "Unknown"),
                    "country": doc.metadata.get("country", "Unknown"),
                    "section": doc.metadata.get("section_id", "Unknown"),
                    "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                for doc in retrieved_docs[:3]
            ]
            
            state.update(retriever_result)
            
            generator_result = generator_agent(state)
            response_data["draft_response"] = generator_result.get("draft_answer", "")
            state.update(generator_result)
            
            critic_result = critic_agent(state)
            response_data["final_response"] = critic_result.get("final_output", {})
            
            # Add metadata
            response_data["metadata"] = {
                "country": [d.metadata.get("country", "Unknown") for d in retrieved_docs],
                "doc_count": len(retrieved_docs),
                "confidence": critic_result.get("final_output", {}).get("confidence_level", "Unknown")
            }
        else:
            response_data["metadata"] = {
                "type": "missing_variables",
                "requires_followup": True
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/examples', methods=['GET'])
def examples():
    """Get example queries"""
    return jsonify({
        "examples": [
            "What are the onboarding requirements for a new hire in Poland?",
            "Can I terminate during probation in Germany?",
            "What is the notice period in France for an employee with 2 years tenure?",
            "Can we terminate a pregnant employee in Germany?",
            "An employee is being transferred from Germany to Austria. What notice period applies?",
            "What are the vacation rules in Italy?",
            "What termination rules apply to a temporary contract worker in France?",
        ]
    }), 200

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════╗
║         EOR COPILOT - REST API SERVER                          ║
║                                                                ║
║  Starting server on: http://127.0.0.1:5000                    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize vector store at startup
    if not initialize_vector_store():
        print("\n⚠️  WARNING: Vector store initialization failed")
        print("   The web interface will still work, but queries will fail")
        print("   Make sure 'docker-compose up --build' is running in another terminal\n")
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║  USAGE:                                                        ║
║  • Web Interface: http://127.0.0.1:5000                        ║
║  • Health check: curl http://127.0.0.1:5000/health            ║
║  • Status check: curl http://127.0.0.1:5000/status            ║
║  • Get examples: curl http://127.0.0.1:5000/examples          ║
║  • Send query:   curl -X POST http://127.0.0.1:5000/query \\   ║
║                    -H "Content-Type: application/json" \\       ║
║                    -d '{"question":"Your question here"}'      ║
║                                                                ║
║  Press Ctrl+C to stop the server                              ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='127.0.0.1', port=5000, debug=False)

