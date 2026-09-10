# src/database_agent/graph/builder.py

from langgraph.graph import END, StateGraph

from database_agent.graph.nodes.chart_decider import chart_decider_node
from database_agent.graph.nodes.compiler import compiler_node, compiler_routing
from database_agent.graph.nodes.executor import executor_node, executor_routing
from database_agent.graph.nodes.give_up import give_up_node
from database_agent.graph.nodes.interpreter import interpreter_node
from database_agent.graph.nodes.query_writer import query_writer_node
from database_agent.graph.state import AgentState


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("query_writer", query_writer_node)
    graph.add_node("compiler", compiler_node)
    graph.add_node("executor", executor_node)
    graph.add_node("interpreter", interpreter_node)
    graph.add_node("chart_decider", chart_decider_node)
    graph.add_node("give_up", give_up_node)

    graph.set_entry_point("query_writer")

    graph.add_edge("query_writer", "compiler")

    graph.add_conditional_edges(
        "compiler",
        compiler_routing,
        {
            "executor": "executor",
            "query_writer": "query_writer",
            "give_up": "give_up",
        },
    )

    graph.add_conditional_edges(
        "executor",
        executor_routing,
        {
            "interpreter": "interpreter",
            "query_writer": "query_writer",
            "give_up": "give_up",
        },
    )

    graph.add_edge("interpreter", "chart_decider")
    graph.add_edge("chart_decider", END)
    graph.add_edge("give_up", END)

    return graph.compile()


_compiled_graph = None


def get_agent_graph():
    """
    Returns the compiled graph, building it once and reusing it, since
    the graph structure itself never changes between requests, only the
    state passed into invoke() does.
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph