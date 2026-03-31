from langgraph.graph import StateGraph, START, END
from backend.agents.state import AgentState
from backend.agents.nodes import (
    supervisor_node,
    search_node,
    dedupe_node,
    analyze_node,
    writer_node,
)

def build_graph():
    graph = StateGraph(AgentState)

    #节点
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("search", search_node)
    graph.add_node("dedupe", dedupe_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("writer", writer_node)

    # 边
    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "search")
    graph.add_edge("search", "dedupe")
    graph.add_edge("dedupe", "analyze")
    graph.add_edge("analyze", "writer")
    graph.add_edge("writer", END)

    return graph.compile()

papyrus_graph = build_graph()