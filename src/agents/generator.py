from src.config import OPENAI_API_KEY


# validate key at import time so errors show early
if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("your"):
    raise ValueError("OPENAI_API_KEY is not configured correctly; check your .env file or environment variables.")

def generator_agent(state: dict) -> dict:
    """Uses OpenAI to generate a draft based ONLY on retrieved context."""
    if state.get("final_output"): return state
    print("[Generator Agent] Drafting response via OpenAI...")
    
    docs = state.get("retrieved_docs", [])
    if not docs:
        return {**state, "draft_answer": "INSUFFICIENT_DATA"}

    context = "\n\n".join([d.page_content for d in docs])

    # perform imports lazily so that the module can be imported without openai pkg
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError as e:
        raise ImportError("langchain-openai and langchain-core are required for generation") from e

    # use a budget‑friendly model for local testing and development.
    # `gpt-3.5-turbo` (or the even smaller `gpt-3.5-mini`) dramatically reduces
    # billing while still providing reasonable conversational quality.  In a
    # production deployment we will swap this back to gpt-4o or another higher‑
    # tier model.
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, api_key=OPENAI_API_KEY)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an HR compliance expert. Answer based ONLY on the provided context. If the context doesn't contain information, say 'Not found in provided context.'"),
        ("human", "Context:\n{context}\n\nQuestion: {query}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"context": context, "query": state["query"]})
    
    return {**state, "draft_answer": response.content}