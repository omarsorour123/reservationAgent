# src/services/reservation_service.py
from langchain_core.messages import HumanMessage
from core.graph import create_reservation_graph

class ReservationService:
    """Service layer for handling the reservation agent interactions."""
    
    def __init__(self):
        self.graph = create_reservation_graph()
        # Store active conversations by thread ID
        self.conversations = {}
    
    def process_message(self, thread_id, user_message):
        """
        Process a user message through the LangGraph reservation assistant.
        
        Args:
            thread_id (str): Unique identifier for the conversation
            user_message (str): User's message content
        
        Returns:
            dict: Response containing thread_id, messages, and response text
        """
        # Initialize or retrieve conversation history
        if thread_id not in self.conversations:
            messages = [HumanMessage(content=user_message)]
        else:
            messages = self.conversations[thread_id].copy()
            messages.append(HumanMessage(content=user_message))
        
        # Process the message through the graph
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke({"messages": messages}, config)
        
        # Update conversation history
        self.conversations[thread_id] = result["messages"]
        
        # Extract the response from the last message
        latest_message = result["messages"][-1]
        response_text = latest_message.content if hasattr(latest_message, "content") else str(latest_message)
        
        return {
            "thread_id": thread_id,
            "messages": result["messages"],
            "response": response_text
        }
    
    def get_conversation(self, thread_id):
        """Get the current conversation for a thread ID."""
        return self.conversations.get(thread_id, [])
    
    def list_threads(self):
        """List all active conversation threads."""
        return list(self.conversations.keys())
    
    def delete_thread(self, thread_id):
        """Delete a conversation thread."""
        if thread_id in self.conversations:
            del self.conversations[thread_id]
            return True
        return False

# Singleton instance for use across the application
reservation_service = ReservationService()