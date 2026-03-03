from src.schemas import CopilotResponse, Citation

def critic_agent(state: dict) -> dict:
    """Verifies the draft and assigns confidence and escalation rules."""
    if state.get("final_output"): return state
    print("[Critic Agent] Verifying draft and enforcing safety guardrails...")
    
    draft = state["draft_answer"]
    docs = state.get("retrieved_docs", [])
    query = state["query"].lower()
    
    citations = [
        Citation(doc_id=d.metadata.get("doc_id", "Unknown"), 
                 section=d.metadata.get("section", "Unknown"), 
                 timestamp=d.metadata.get("updated_at", "Unknown")) 
        for d in docs
    ]

    # Base response with verified context
    response = CopilotResponse(
        final_response=draft,
        citations=citations,
        confidence_level="High",
        confidence_reason="Answer generated directly from verified Qdrant context."
    )
    
    # SCENARIO 4C: Handle INSUFFICIENT_DATA - no relevant documents found
    if draft == "INSUFFICIENT_DATA" or len(docs) == 0:
        response.final_response = "I cannot find specific policies regarding this query in the knowledge base."
        response.confidence_level = "Low"
        response.confidence_reason = "No relevant context found in the knowledge base."
        response.escalation_recommendation = "ESCALATE: Please contact the Legal/Compliance team for manual policy verification."
        response.citations = []
        print(f" [INSUFFICIENT_DATA] Escalating query due to lack of coverage.")
    
    # SCENARIO 4D: High-Risk / Adversarial detection
    # Detect pregnancy-related queries
    elif "pregnant" in query or "pregnancy" in query or "maternity" in query:
        response.confidence_level = "Low"
        response.confidence_reason = "Query involves pregnancy - a highly protected legal class requiring specialized legal counsel."
        response.escalation_recommendation = "🚨 CRITICAL ESCALATION: This query involves pregnancy-related matters. IMMEDIATELY consult with Local Legal Counsel before proceeding. Pregnancy discrimination is illegal in most jurisdictions."
        # Still show the draft but with strong escalation warning
        print(f" [HIGH-RISK: PREGNANCY] Escalating for legal review with provided context.")
    
    # Detect discrimination-related queries
    elif "discriminat" in query or "harassment" in query or "retaliat" in query:
        response.confidence_level = "Low"
        response.confidence_reason = "Query involves potential discrimination or unlawful retaliation - requires specialized legal review."
        response.escalation_recommendation = "🚨 CRITICAL ESCALATION: This query involves potential discrimination or retaliation. CONSULT LOCAL LEGAL COUNSEL IMMEDIATELY before taking any action. These matters have significant legal liability."
        print(f" [HIGH-RISK: DISCRIMINATION/RETALIATION] Escalating for legal review.")
    
    # SCENARIO 4A: Low confidence due to insufficient supporting context
    elif len(docs) < 2:
        response.confidence_level = "Medium"
        response.confidence_reason = "Limited supporting context found. Answer may be incomplete."
        response.escalation_recommendation = "Consider consulting Local Legal Counsel for comprehensive guidance."
        print(f" [LOW CONFIDENCE] Only {len(docs)} supporting document(s) found.")
    
    return {**state, "final_output": response.model_dump()}