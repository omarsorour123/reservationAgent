# src/core/graph.py
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState
from database.database_operations import check_availability, reserve_room
from agents.ReservationAgent import reservation_assistant_agent
from langgraph.checkpoint.memory import MemorySaver

def create_reservation_graph():
    """Create and return the LangGraph for reservation handling."""
    # Define your tools
    tools = [check_availability, reserve_room]
    
    # Create the state graph
    builder = StateGraph(MessagesState)
    memory = MemorySaver()
    
    # Add nodes
    builder.add_node('assistant', reservation_assistant_agent)
    builder.add_node('tools', ToolNode(tools))
    
    # Add edges
    builder.add_edge(START, 'assistant')
    builder.add_conditional_edges('assistant', tools_condition, ['tools', END])
    builder.add_edge('tools', 'assistant')
    
    # Compile the graph
    graph = builder.compile(checkpointer=memory)
    
    return graph