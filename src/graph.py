from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

from src.nodes.planner_node import planner
from src.nodes.searcher_node import searcher
from src.nodes.analyzer_node import analyzer_node
from src.nodes.synthesizer_node import synthesizer_node
from src.nodes.evaluator_node import evaluator_node

# Define the state
class AgentState(TypedDict):
    query: str
    plan: list[str]
    search_results: Annotated[list[str], operator.add]
    analyzed_data: Annotated[list[str], operator.add]
    report: str
    evaluation: str
    loop_count: int

def router(state):
    print("---ROUTER---")
    loop_count = state.get("loop_count", 0)
    if "sufficient" in state["evaluation"].lower() or loop_count >= 2:
        return "synthesizer"
    else:
        return "planner"

# Define the graph
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner)
workflow.add_node("searcher", searcher)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("evaluator", evaluator_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "searcher")
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("analyzer", "evaluator")
workflow.add_conditional_edges(
    "evaluator",
    router,
    {
        "synthesizer": "synthesizer",
        "planner": "planner",
    },
)
workflow.add_edge("synthesizer", END)
