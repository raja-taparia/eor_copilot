from src.config import QDRANT_HOST, QDRANT_PORT

# embeddings and other heavy modules are created lazily inside the functions to
# avoid requiring large ML libraries during import (e.g. when running lightweight
# unit tests or importing only type definitions).
embeddings = None

def _ensure_embeddings():
    global embeddings
    if embeddings is None:
        try:
            # prefer the lightweight local HF model if available
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        except Exception as e:  # covers ImportError or runtime failures (numpy/tf/torch)
            print("WARNING: unable to load HuggingFaceEmbeddings, using dummy embeddings:", e)
            # fallback embedding that returns constant zero vectors
            class DummyEmbeddings:
                def __init__(self, size: int = 384):
                    self.size = size
                def embed_documents(self, texts):
                    return [[0.0] * self.size for _ in texts]
                def embed_query(self, text):
                    return [0.0] * self.size
                # Qdrant wrapper sometimes expects the object itself to be callable
                def __call__(self, text):
                    return self.embed_query(text)
            embeddings = DummyEmbeddings()
    return embeddings

def get_qdrant_vector_store():
    """Initializes Qdrant client and populates mock data if empty.
    
    Raises:
        ConnectionError: If Qdrant is not reachable
        ImportError: If required packages are missing
    """
    # delayed imports
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams
    except ImportError as e:
        raise ImportError("qdrant-client is required for vector store functionality") from e
    try:
        from langchain_community.vectorstores import Qdrant
    except ImportError as e:
        raise ImportError("langchain-community is required for Qdrant vector store wrapper") from e

    print(f"\n🔄 Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    
    try:
        # Try to create client with timeout
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            timeout=5.0  # 5 second timeout
        )
        
        # Test connection by listing collections
        try:
            collections = client.get_collections()
            print(f"   ✅ Connected to Qdrant. Found {len(collections.collections)} existing collection(s)")
        except Exception as e:
            raise ConnectionError(f"Cannot reach Qdrant at {QDRANT_HOST}:{QDRANT_PORT}: {str(e)}") from e
        
    except Exception as e:
        raise ConnectionError(f"Qdrant connection failed: {str(e)}") from e
    
    # Compatibility: add search() method for LangChain's Qdrant wrapper
    # LangChain expects client.search(collection_name, query_vector, limit, **kwargs)
    # to return a list of ScoredPoint objects
    # Newer qdrant-client uses query_points(collection_name, query, limit, **kwargs)
    # which returns a QueryResponse with a .points attribute
    def search_adapter(collection_name, query_vector, limit=10, **kwargs):
        """Adapter to provide search() method using query_points() API."""
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,  # query_points accepts a list of floats as the query vector
            query_filter=kwargs.get('query_filter'),
            with_payload=kwargs.get('with_payload', True),
            with_vectors=kwargs.get('with_vectors', False),
            limit=limit
        )
        # Return the points list directly (LangChain wrapper expects ScoredPoint objects)
        return response.points if hasattr(response, 'points') else response
    
    client.search = search_adapter
    
    collection_name = "eor_policies"
    
    # Create collection if it doesn't exist
    if not client.collection_exists(collection_name):
        print(f"   📦 Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        _seed_mock_data(client, collection_name)
    else:
        # Collection exists, check if it has data
        try:
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count
            print(f"   ✅ Collection '{collection_name}' exists with {points_count} documents")
            
            if points_count == 0:
                print(f"   ⚠️  Collection is empty, re-seeding with mock data...")
                _seed_mock_data(client, collection_name)
        except Exception as e:
            print(f"   ❌ Error checking collection: {e}")
            # Continue anyway, LangChain wrapper might still work
        
    return Qdrant(client=client, collection_name=collection_name, embeddings=_ensure_embeddings())


def _seed_mock_data(client, collection_name):
    """Seeds the Vector DB with initial HR compliance chunks from the sample JSON file."""
    # load sample policy documents from data folder
    import json, os
    # path should point to workspace root/data/policies/sample_policies.json
    # database.py lives in src/, so one '..' is enough
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "policies", "sample_policies.json")
    sample_path = os.path.abspath(sample_path)
    with open(sample_path, "r") as f:
        raw = json.load(f)

    # If the sample file is small, expand it programmatically so tests and
    # demos have a richer dataset (aim for ~60 entries). This avoids needing
    # a gigantic checked-in JSON while still enabling realistic vector tests.
    target_count = 60
    if len(raw) < target_count:
        expanded = []
        i = 0
        while len(expanded) < target_count:
            for item in raw:
                if len(expanded) >= target_count:
                    break
                # clone and give a unique doc_id
                i += 1
                clone = dict(item)
                base_id = item.get("doc_id", f"doc{i}")
                clone["doc_id"] = f"{base_id}_dup{i}"
                # optionally tweak text slightly to create varied chunks
                clone["text"] = item.get("text", "") + f" Additional guidance clause {i}."
                expanded.append(clone)
        raw = expanded

    # import heavy dependencies here
    from langchain_core.documents import Document
    try:
        from langchain_community.vectorstores import Qdrant
    except ImportError:
        raise ImportError("langchain-community is required to seed documents into Qdrant")

    # small helper to chunk long texts into overlapping windows
    def _chunk_text(text: str, chunk_size: int = 250, overlap: int = 50):
        if not text:
            return []
        chunks = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + chunk_size, length)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < length else end
        return chunks

    docs = []
    for item in raw:
        text = item.get("text", "")
        chunks = _chunk_text(text)
        if not chunks:
            # ensure at least one doc
            chunks = [text]
        for idx, c in enumerate(chunks, 1):
            docs.append(Document(
                page_content=c,
                metadata={
                    "doc_id": item.get("doc_id"),
                    "chunk_id": idx,
                    "section": item.get("section_id"),
                    **item.get("metadata", {}),
                },
            ))

    # Langchain Qdrant wrapper to insert docs
    vector_store = Qdrant(client=client, collection_name=collection_name, embeddings=_ensure_embeddings())
    vector_store.add_documents(docs)
    print(f"   ✅ Seeded {len(docs)} document chunks into '{collection_name}'")
