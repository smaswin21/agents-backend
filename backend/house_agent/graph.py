
"""
LangGraph state graph for the household agent.
Defines the LLM interaction logic and tool execution flow.
"""
import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from .config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from .state import AgentState
from .tools import (
    add_numbers,
    fetch_household_inventory,
    fetch_household_budget,
    analyze_pantry_items,
    add_item_sync,
    bulk_add_items_sync
)

# Define all available tools
TOOLS = [
    StructuredTool.from_function(add_numbers),
    StructuredTool.from_function(fetch_household_inventory),
    StructuredTool.from_function(fetch_household_budget),
    StructuredTool.from_function(analyze_pantry_items),
    StructuredTool.from_function(add_item_sync),
    StructuredTool.from_function(bulk_add_items_sync),
]

SYSTEM_MESSAGE = """You are Household Mediator, an AI assistant that helps housemates stay organized 
by tracking inventory, groceries, and shared expenses.

You have access to the following tools:
- fetch_household_inventory: Get current inventory status for a household
- fetch_household_budget: Get the household's grocery budget
- analyze_pantry_items: Analyze inventory to identify low/out-of-stock items
- add_item_sync: Add a single item to a MongoDB collection (grocery_lists, pantry_items, households, users, agent_runs)
- bulk_add_items_sync: Add multiple items to MongoDB collections in bulk
- add_numbers: Add two numbers (for testing)

IMPORTANT: When you need to save items to the database, you MUST call add_item_sync or bulk_add_items_sync.
Do NOT just say you added something - actually call the tool to save it to MongoDB.

Use these tools to help users understand their household inventory and make shopping decisions.
Be concise, neutral, and proactive about preventing conflicts."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_MESSAGE),
    MessagesPlaceholder("messages")
])


def _parse_args(args):
    """Parse tool arguments from various formats."""
    if args is None:
        return {}
    if isinstance(args, dict):
        return args
    if isinstance(args, (str, bytes, bytearray)):
        return json.loads(args or "{}")
    return json.loads(str(args))


def _exec_tool(name: str, args):
    """Execute a tool by name with parsed arguments."""
    parsed = _parse_args(args)
    
    if name == "add_numbers":
        return add_numbers(**parsed)
    elif name == "fetch_household_inventory":
        return fetch_household_inventory(**parsed)
    elif name == "fetch_household_budget":
        return fetch_household_budget(**parsed)
    elif name == "analyze_pantry_items":
        return analyze_pantry_items(**parsed)
    elif name == "add_item_sync":
        return add_item_sync(**parsed)
    elif name == "bulk_add_items_sync":
        return bulk_add_items_sync(**parsed)
    
    return f"Unknown tool: {name}"


def call_model(state: AgentState) -> AgentState:
    """
    Main agent logic: invoke LLM with tools and handle tool calls.
    Allows up to 3 rounds of tool use before returning final response.
    """
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0,
    ).bind_tools(TOOLS)

    msgs = state["messages"]

    # Allow up to 3 rounds of tool use
    for _ in range(3):
        ai: AIMessage = llm.invoke(PROMPT.invoke({"messages": msgs}))
        msgs = msgs + [ai]

        # If no tool was called, we're done
        if not getattr(ai, "tool_calls", None):
            return {"messages": [ai]}

        # Execute tools and append results, then loop again
        for tc in ai.tool_calls:
            try:
                result = _exec_tool(tc["name"], tc.get("args"))
                content = result if isinstance(result, str) else json.dumps(result)
            except Exception as e:
                content = f"Error executing tool {tc['name']}: {str(e)}"
            
            msgs.append(ToolMessage(
                tool_call_id=tc["id"],
                name=tc["name"],
                content=content,
            ))

    # Safety: return last message if loop cap hit
    return {"messages": [msgs[-1]]}


def build_graph():
    """Build and return the compiled StateGraph."""
    g = StateGraph(AgentState)
    g.add_node("llm", call_model)
    g.set_entry_point("llm")
    g.add_edge("llm", END)
    return g.compile()