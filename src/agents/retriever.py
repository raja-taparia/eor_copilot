def retriever_agent(state: dict) -> dict:
    """Uses Qdrant and local embeddings to retrieve legal context."""
    if state.get("final_output"): return state
    print(" Executing semantic search in Qdrant...")

    try:
        from src.database import get_qdrant_vector_store
    except ImportError:
        # dependencies missing; return empty retrieval
        return {**state, "retrieved_docs": []}
    
    # Extract country from query if mentioned
    def extract_country_from_query(query: str) -> str:
        """Extract country name from query."""
        countries = [
            "Poland", "Germany", "France", "UK", "United Kingdom", "Spain", 
            "Italy", "Ireland", "Netherlands", "Belgium", "Sweden", "Portugal",
            "Austria", "Denmark", "Finland", "Norway", "Greece", "Czechia",
            "Czech Republic", "Hungary", "Slovakia", "Estonia"
        ]
        query_lower = query.lower()
        for country in countries:
            if country.lower() in query_lower:
                # Normalize country name (e.g., "UK" -> use "UK", "Czech Republic" -> "Czechia")
                if country.lower() in ["uk", "united kingdom"]:
                    return "UK"
                elif country.lower() == "czech republic":
                    return "Czechia"
                return country
        return None
    
    target_country = extract_country_from_query(state["query"])

    def _simple_keyword_search(query: str, k: int = 3):
        """Fallback scanning of the bundled JSON file when vector search fails."""
        import json, os
        from langchain_core.documents import Document
        # compute path relative to workspace root (two levels up from this file)
        path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "policies", "sample_policies.json")
        path = os.path.abspath(path)
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception:
            return []
        q = query.lower()
        results = []
        for item in data:
            text = item.get("text", "")
            if q in text.lower():
                results.append(Document(page_content=text, metadata=item.get("metadata", {})))
                if len(results) >= k:
                    break
        return results

    try:
        vector_store = get_qdrant_vector_store()
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        def _fetch(rtr, query):
            # try known retrieval methods, inspect signatures, and handle
            # async/private variants to be resilient against wrapper changes.
            import inspect, asyncio
            base = [
                "get_relevant_documents",
                "get_relevant_items",
                "get_documents",
                "get",
                "search",
                "invoke",
            ]
            # expand with common internal/async prefixes that some wrappers use
            candidates = []
            for n in base:
                candidates.extend([n, f"_{n}", f"a{n}", f"_a{n}", f"_{'a'+n}"])
            # dedupe while preserving order
            seen = set()
            candidates = [c for c in candidates if not (c in seen or seen.add(c))]

            for name in candidates:
                if hasattr(rtr, name):
                    func = getattr(rtr, name)
                    try:
                        sig = inspect.signature(func)
                    except Exception:
                        sig = None

                    # helper to attempt a synchronous or asynchronous call
                    def _try_call(f, kwargs):
                        # if coroutine function, run it
                        try:
                            if asyncio.iscoroutinefunction(f):
                                return asyncio.run(f(**kwargs))
                            # some callables are bound methods that accept positional
                            # args — prefer kwargs but fall back to positional
                            if kwargs:
                                return f(**kwargs)
                            return f(query)
                        except TypeError:
                            # positional fallback
                            try:
                                return f(query)
                            except Exception:
                                raise

                    # try straightforward call first
                    try:
                        # handle coroutine and sync transparently
                        if inspect.iscoroutinefunction(func):
                            return asyncio.run(func(query))
                        try:
                            return func(query)
                        except TypeError:
                            pass
                    except Exception:
                        # unexpected failure should bubble up for logging
                        raise

                    # if signature available, try to use parameter names
                    if sig is not None:
                        params = list(sig.parameters.values())
                        # drop 'self' if present
                        if params and params[0].name == "self":
                            params = params[1:]
                        if params:
                            # build kwargs intelligently: map the first positional
                            # param to the query, and provide safe defaults for
                            # required keyword-only params (e.g. run_manager=None)
                            kwargs = {}
                            first_assigned = False
                            for p in params:
                                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                                    if not first_assigned:
                                        kwargs[p.name] = query
                                        first_assigned = True
                                    else:
                                        # other positional args: try to supply None or default
                                        if p.default is not inspect._empty:
                                            kwargs[p.name] = p.default
                                        else:
                                            kwargs[p.name] = None
                                elif p.kind == inspect.Parameter.KEYWORD_ONLY:
                                    # supply None for required kws like run_manager
                                    if p.default is not inspect._empty:
                                        kwargs[p.name] = p.default
                                    else:
                                        # common runtime-only managers should be safe as None
                                        kwargs[p.name] = None
                                elif p.kind == inspect.Parameter.VAR_POSITIONAL:
                                    # nothing to add for *args
                                    continue
                                elif p.kind == inspect.Parameter.VAR_KEYWORD:
                                    # **kwargs can accept extras
                                    continue
                            try:
                                return _try_call(func, kwargs)
                            except Exception:
                                pass
                        # try common keyword alternatives
                        for key in ("query_text", "query", "q", "input", "inputs", "prompt", "text", "input_text"):
                            if sig and key in sig.parameters:
                                try:
                                    return _try_call(func, {key: query})
                                except Exception:
                                    pass

                    # as a last effort, if retriever itself is callable, try that
                    if callable(rtr):
                        try:
                            if inspect.iscoroutinefunction(rtr):
                                return asyncio.run(rtr(query))
                            return rtr(query)
                        except Exception:
                            pass
                    # nothing worked for this candidate: continue
                    continue

            available = [n for n in candidates if hasattr(rtr, n)]
            raise AttributeError(f"no compatible retrieval method found (checked {base}, available {available})")

        try:
            docs = _fetch(retriever, state["query"])
            
            # Filter by country if one was detected in the query
            if target_country:
                print(f" [Country filter] Filtering results for: {target_country}")
                docs = [d for d in docs if d.metadata.get("country") == target_country]
                print(f" Retrieved {len(docs)} document(s) for {target_country}")
            
        except Exception as inner:
            print(f"Retriever warning: {inner}, falling back to keyword scan")
            # dump some introspection to help debugging if this occurs frequently
            print(" Retriever object methods:", [m for m in dir(retriever) if not m.startswith("__")][:40])
            docs = _simple_keyword_search(state["query"])
            
            # Apply country filter to keyword search results too
            if target_country:
                docs = [d for d in docs if d.metadata.get("country") == target_country]
    except Exception as e:
        # if the client isn't available (e.g. no qdrant running), fall back
        print(f"Retriever error: {e}")
        docs = _simple_keyword_search(state["query"])

    return {**state, "retrieved_docs": docs}
