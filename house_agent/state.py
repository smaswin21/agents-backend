# state.py

# will store conversation memory inside the graph
from typing_extensions import TypedDict, Annotated
from typing import List
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # Append-only message list across the graph execution
    messages: Annotated[List[BaseMessage], operator.add]
