"""
CLI runner for testing the household agent locally.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from .graph import build_graph


def main():
    app = build_graph()
    print("🏠 Household Agent Ready!")
    print("Ask about inventory, budget, or pantry status.")
    print("Type 'exit' to quit.\n")

    state = {"messages": []}
    
    while True:
        user_input = input("\n👤 User: ").strip()
        
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
            
        if not user_input:
            continue
        
        # Add user message
        state["messages"].append(HumanMessage(content=user_input))
        
        # Run the graph
        try:
            state = app.invoke(state)
            
            # Get the last message (agent's response)
            last_msg = state["messages"][-1]
            print(f"\n🤖 Agent: {last_msg.content}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()