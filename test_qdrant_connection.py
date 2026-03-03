#!/usr/bin/env python3
"""
Diagnostic script to test Qdrant connectivity and vector store initialization
Run this before running api_server.py to diagnose connection issues
"""

import os
import sys
import time
from pathlib import Path

# By default the script respects whatever QDRANT_HOST/PORT are in the
# environment (e.g. from .env).  Previously we forced localhost which
# masked configuration problems when running on the host.
# os.environ['QDRANT_HOST'] = '127.0.0.1'
# os.environ['QDRANT_PORT'] = '6333'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_qdrant_basic():
    """Test basic Qdrant connectivity"""
    print("\n" + "="*70)
    print("1️⃣  TESTING BASIC QDRANT CONNECTIVITY")
    print("="*70)
    
    try:
        from qdrant_client import QdrantClient
        
        effective_host = os.getenv('QDRANT_HOST', '127.0.0.1')
        print(f"   Attempting to connect to Qdrant at {effective_host}:6333...")
        client = QdrantClient(host=effective_host, port=6333, timeout=5.0)
        
        collections = client.get_collections()
        print(f"   ✅ Successfully connected to Qdrant!")
        print(f"   ✅ Found {len(collections.collections)} collection(s)")
        
        for col in collections.collections:
            print(f"      • {col.name}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)[:100]}")
        print("\n   💡 TROUBLESHOOTING:")
        print("      • Is Qdrant running? Try: docker-compose up --build")
        print("      • Is port 6333 exposed? Check docker-compose.yml")
        print("      • Run 'docker ps' to verify Qdrant container is running")
        return False
    
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)[:100]}")
        return False

def test_embeddings():
    """Test embeddings model"""
    print("\n" + "="*70)
    print("2️⃣  TESTING EMBEDDINGS MODEL")
    print("="*70)
    
    try:
        print("   Loading HuggingFace embeddings (all-MiniLM-L6-v2)...")
        from langchain_huggingface import HuggingFaceEmbeddings
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Test embedding
        test_text = "What is the notice period for termination?"
        result = embeddings.embed_query(test_text)
        
        print(f"   ✅ Embeddings model loaded successfully!")
        print(f"   ✅ Embedding dimension: {len(result)}")
        return True
    
    except Exception as e:
        print(f"   ❌ Failed to load embeddings: {str(e)[:100]}")
        print("   💡 Make sure torch/numpy are installed: pip install -r requirements.txt")
        return False

def test_vector_store():
    """Test full vector store initialization"""
    print("\n" + "="*70)
    print("3️⃣  TESTING VECTOR STORE INITIALIZATION")
    print("="*70)
    
    try:
        from database import get_qdrant_vector_store
        
        print("   Initializing vector store...")
        store = get_qdrant_vector_store()
        
        print("   ✅ Vector store initialized successfully!")
        
        # Try a simple search
        print("\n   Testing vector search...")
        results = store.similarity_search("termination notice period", k=2)
        
        print(f"   ✅ Search returned {len(results)} results")
        for i, result in enumerate(results, 1):
            country = result.metadata.get("country", "Unknown")
            section = result.metadata.get("section", "Unknown")
            snippet = result.page_content[:80] + "..." if len(result.page_content) > 80 else result.page_content
            print(f"      [{i}] {country} | {section}")
            print(f"          {snippet}")
        
        return True
    
    except ConnectionError as e:
        print(f"   ❌ Connection error: {str(e)[:100]}")
        print("   💡 Qdrant is not running. Make sure docker-compose is up")
        return False
    
    except Exception as e:
        print(f"   ❌ Vector store initialization failed: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return False

def test_api_server():
    """Test API server connectivity"""
    print("\n" + "="*70)
    print("4️⃣  TESTING API SERVER ROUTES")
    print("="*70)
    
    try:
        from api_server import app, test_qdrant_connection
        
        print("   Testing Flask app routes...")
        with app.test_client() as client:
            # Test /health
            response = client.get('/health')
            print(f"   GET /health → {response.status_code}")
            if response.status_code == 200:
                print(f"      Response: {response.get_json()}")
            
            # Test /status
            response = client.get('/status')
            print(f"   GET /status → {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"      Vector store: {data.get('vector_store_initialized')}")
            
            # Test /examples
            response = client.get('/examples')
            print(f"   GET /examples → {response.status_code}")
        
        print("   ✅ API routes are accessible")
        return True
    
    except Exception as e:
        print(f"   ⚠️  API test skipped: {str(e)[:100]}")
        return False

def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  EOR COPILOT - QDRANT CONNECTION DIAGNOSTIC                    ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Run tests
    results.append(("Basic Qdrant Connection", test_qdrant_basic()))
    results.append(("Embeddings Model", test_embeddings()))
    results.append(("Vector Store Init", test_vector_store()))
    results.append(("API Server Routes", test_api_server()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 All checks passed! Ready to run:")
        print("      1. docker-compose up --build")
        print("      2. python api_server.py")
        print("      3. Visit http://127.0.0.1:5000")
    else:
        print("\n   ❌ Some checks failed. Please fix the issues above.")
        print("   💡 Most common issue: Qdrant not running")
        print("      → Run: docker-compose up --build")
    
    print()

if __name__ == '__main__':
    main()
