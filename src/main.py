import json
from src.graph import run_copilot

def demo():
    questions = [
        "What are the onboarding requirements for a new hire in Poland?",
        "Can I terminate during probation in Germany?",
        "What is the notice period in France for an employee with 2 years tenure?",
        "Can we terminate a pregnant employee in Germany?",
        "An employee is being transferred from Germany to Austria. What notice period applies?",
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n=======================================================")
        print(f" SCENARIO {i}: {q}")
        print(f"=======================================================")
        
        # Run the graph
        result, state = run_copilot(q)
        
        print("\n--- 1. RETRIEVED EVIDENCE ---")
        if state.get("retrieved_docs"):
            for doc in state["retrieved_docs"]:
                print(f"Doc ID: {doc.metadata.get('doc_id')} | Content: {doc.page_content}")
        else:
            print("No evidence retrieved or skipped due to Supervisor halt.")

        print("\n--- 2. DRAFT ANSWER ---")
        print(state.get("draft_answer", "No draft generated."))

        print("\n--- 3. VERIFIER FEEDBACK ---")
        if "confidence_reason" in result:
             print(f"Critic Assessment: {result['confidence_reason']}")
             if result.get("escalation_recommendation"):
                 print(f"CRITICAL FLAG: {result['escalation_recommendation']}")
        else:
             print("Verifier skipped (handled by Supervisor).")

        print("\n--- 4. FINAL ANSWER + CITATIONS + CONFIDENCE ---")
        print(json.dumps(result, indent=2))
        print("\n")

if __name__ == "__main__":
    demo()