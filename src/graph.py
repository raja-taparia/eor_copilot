from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from src.agents.supervisor import supervisor_agent
from src.agents.retriever import retriever_agent
from src.agents.generator import generator_agent
from src.agents.critic import critic_agent

# 1. Define the State for the Multi-Agent Graph
class AgentState(TypedDict):
    query: str
    retrieved_docs: List
    draft_answer: str
    final_output: dict

# 2. Define Conditional Routing Logic
def route_from_supervisor(state: AgentState) -> str:
    """
    Determines the next node after the Supervisor.
    If the Supervisor detects missing parameters and populates final_output,
    the graph halts early to save compute/API costs.
    """
    if state.get("final_output"):
        return END
    return "Retriever"

# 3. Build and Compile the Graph
def build_copilot_graph():
    """
    Constructs the Supervisor-Worker-Critic LangGraph architecture.
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes (Agents)
    workflow.add_node("Supervisor", supervisor_agent)
    workflow.add_node("Retriever", retriever_agent)
    workflow.add_node("Generator", generator_agent)
    workflow.add_node("Critic", critic_agent)
    
    # Define the Control Flow
    workflow.set_entry_point("Supervisor")
    
    # Conditional Edge: Supervisor either hands off to Retriever, or halts (END)
    workflow.add_conditional_edges(
        "Supervisor", 
        route_from_supervisor, 
        {
            END: END, 
            "Retriever": "Retriever"
        }
    )
    
    # Linear Edges for the rest of the workflow
    workflow.add_edge("Retriever", "Generator")
    workflow.add_edge("Generator", "Critic")
    workflow.add_edge("Critic", END)
    
    return workflow.compile()

# 4. Execution Wrapper
def run_copilot(query: str):
    """
    Entry point to invoke the graph with a user query.
    Returns both the final output payload and the entire state for tracing.
    """
    graph = build_copilot_graph()
    initial_state = AgentState(query=query, retrieved_docs=[], draft_answer="", final_output={})
    
    # Invoke the state graph
    result = graph.invoke(initial_state)
    
    return result.get("final_output", {}), result