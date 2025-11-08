# run.py
from langchain_core.messages import HumanMessage, SystemMessage
from .graph import build_graph

# def main():
#     app = build_graph()
#     print("LangGraph x GPT-5 agent (nano). Type 'exit' to quit.")
#     state = {"messages": []}
    
    
#     state = {
#         "messages": [
#             SystemMessage(
#                 content=(
#                     "You are Household Mediator, an AI assistant that helps housemates stay organized "
#                     "by tracking inventory, groceries, and shared expenses. "
#                     "You can call tools to add or list items in the pantry, manage grocery lists, "
#                     "and record expenses. "
#                     "Be concise, neutral, and proactive about preventing conflicts."
#                 ) # ADD HERE THAT YOU WILL BE CALLING TOOLS
#             )
#         ]
#     }

#     while True:
#         user = input("\Tenant: ").strip()
#         if not user:
#             continue
#         if user.lower() in {"exit", "quit"}:
#             break

#         state["messages"].append(HumanMessage(content=user))
#         # Run one turn through the graph
#         state = app.invoke(state)
#         # Find last assistant message
#         last = state["messages"][-1]
#         print(f"Agent: {last.content}")

# if __name__ == "__main__":
#     main()


def main():
    app = build_graph()
    print("LangGraph tool-call test. Type 'exit' to quit.")

    state = {"messages": [SystemMessage(content="You can add numbers using the add_numbers tool.")]}
    while True:
        user = input("\nYou: ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        if not user:
            continue
        state["messages"].append(HumanMessage(content=user))
        state = app.invoke(state)
        print("Agent:", state["messages"][-1].content)

if __name__ == "__main__":
    main()
