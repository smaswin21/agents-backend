# house_agent/graph.py
# file to define the StateGraph for the agent and the LLM interaction logic
import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from .config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from .state import AgentState  # or maybe dict ?
from .tools import add_numbers

TOOLS = [StructuredTool.from_function(add_numbers)]

PROMPT = ChatPromptTemplate.from_messages([MessagesPlaceholder("messages")])

def _parse_args(args):
    if args is None:
        return {}
    if isinstance(args, dict):
        return args
    if isinstance(args, (str, bytes, bytearray)):
        return json.loads(args or "{}")
    return json.loads(str(args))

def _exec_tool(name: str, args):
    parsed = _parse_args(args)
    if name == "add_numbers":
        return add_numbers(**parsed)
    return f"unknown tool: {name}"

def call_model(state: AgentState) -> AgentState:
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0,
    ).bind_tools(TOOLS) # DO THIS TO BIND TOOLS

    msgs = state["messages"]

    # allow up to 3 rounds of tool use
    for _ in range(3):
        ai: AIMessage = llm.invoke(PROMPT.invoke({"messages": msgs}))
        msgs = msgs + [ai]

        # if no tool was called, we're done
        if not getattr(ai, "tool_calls", None):
            return {"messages": [ai]}

        # execute tools and append results, then loop again
        for tc in ai.tool_calls:
            result = _exec_tool(tc["name"], tc.get("args"))
            msgs.append(ToolMessage(
                tool_call_id=tc["id"],
                name=tc["name"],
                content=result if isinstance(result, str) else json.dumps(result),
            ))

    # safety: return last message if loop cap hit
    return {"messages": [msgs[-1]]}

def build_graph(): # to be called from run.py
    # builds and returns the StateGraph
    g = StateGraph(AgentState)  
    g.add_node("llm", call_model)
    g.set_entry_point("llm")
    g.add_edge("llm", END)
    return g.compile()
