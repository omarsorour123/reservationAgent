from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from IPython.display import Image, display
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from database.database_operations import check_availability, reserve_room
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import MessagesState, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from agents import reservation_assistant_agent
from langgraph.checkpoint.memory import MemorySaver
# Define your tools

def tools_condition(state):
    """Determine if we should route to the tools node."""
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return 'tools'
    return END

tools = [check_availability, reserve_room]

# Create the state graph
builder = StateGraph(MessagesState)
memory = MemorySaver()
# Add nodes - fix the spelling of "assistant" to be consistent
builder.add_node('assistant', reservation_assistant_agent)
builder.add_node('tools', ToolNode(tools))

# Add edges
builder.add_edge(START, 'assistant')
builder.add_conditional_edges("assistant", tools_condition,['tools', END])
builder.add_edge('tools', 'assistant')

# Compile the graph
graph = builder.compile(checkpointer=memory)
image_bytes = graph.get_graph(xray=True).draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(image_bytes)

counter = 0
config = {"configurable": {'thread_id': '1'}}
while True:
    user_input = input('User ')
    if user_input == 'bye':
        break
    
    if counter == 0:
        messages = [HumanMessage(content=user_input)]
    else:
        messages.append(HumanMessage(content=user_input))
    
    # The invoke method returns a dictionary
    result = graph.invoke({'messages': messages}, config)
    
    # Update our messages with the result
    messages = result['messages']
    
    # Print the last message
    messages[-1].pretty_print()
    counter += 1