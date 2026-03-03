from typing import Dict

def supervisor_agent(state: dict) -> dict:
    """Analyzes the user query for missing parameters and asks clarifying questions."""
    query = state["query"].lower()
    print("\n Analyzing Intent...")
    
    # Detect missing tenure information for specific countries' notice period rules
    missing_tenure_countries = ["france", "germany", "italy"]
    if any(country in query for country in missing_tenure_countries) and "notice" in query and "tenure" not in query and "years" not in query and "months" not in query:
        country = next((c for c in missing_tenure_countries if c in query), "the employee")
        print(f" Missing critical parameter: Employee tenure.")
        return {
            **state,
            "final_output": {
                "final_response": f"To accurately determine the notice period requirements, I need more information about the employee.",
                "citations": [],
                "confidence_level": "Low",
                "confidence_reason": "Missing required variable: employee tenure/years of service.",
                "escalation_recommendation": None,
                "follow_up_questions": [f"How long has the employee been with the company? (in months or years)", "Is there a specific contract or collective agreement?"]
            }
        }
    
    # Detect missing country information
    countries = ["poland", "germany", "france", "uk", "united kingdom", "spain", "italy", "ireland", "netherlands", "belgium", "sweden"]
    has_country = any(c in query for c in countries)
    if not has_country and ("regulation" in query or "law" in query or "requirement" in query or "policy" in query):
        print(" Missing critical parameter: Country/jurisdiction.")
        return {
            **state,
            "final_output": {
                "final_response": "To provide accurate legal guidance, I need to know which country's employment law applies.",
                "citations": [],
                "confidence_level": "Low",
                "confidence_reason": "Missing required variable: country/jurisdiction.",
                "escalation_recommendation": None,
                "follow_up_questions": ["Which country's employment law applies to this situation?", "Where is the employee located?"]
            }
        }
    
    # Detect high-risk keywords that bypass normal flow
    high_risk_keywords = ["pregnant", "pregnancy", "discriminat", "harass", "retaliat"]
    if any(keyword in query for keyword in high_risk_keywords):
        print(" HIGH-RISK QUERY detected. Routing to Critic for escalation.")
        # Don't halt here - let it flow to critic agent
    
    return state