from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, trim_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from config import Config
from tools import tools_list
from prompt import prompt1
from db_maintenance import cleanup_if_needed
import sqlite3
import os

os.environ["USER_AGENT"] = "MyAgent/1.0"

# ── DB Maintenance ─────────────────────────────
# LangGraph checkpoints grow O(n^2); auto-prune old ones if the DB gets too big.
_cleanup_result = cleanup_if_needed()
if _cleanup_result:
    _pc, _pw, _before, _after = _cleanup_result
    print(f"[db_maintenance] chatbot.db pruned: {_pc} checkpoints removed, "
          f"{_before:.1f} MB -> {_after:.1f} MB")

# ── Message trimming ───────────────────────────
# Keep only the last 20 messages so checkpoints stay small forever.
trimmer = trim_messages(
    max_tokens=20,
    strategy="last",
    token_counter=len,  # counts messages (not tokens)
    include_system=True,
    allow_partial=False,
    start_on="human",
)

# ── Tool output truncation ─────────────────────
# Tool results (search dumps, email bodies) are the biggest checkpoint bloat
# source — cap them before they enter the conversation state.
MAX_TOOL_OUTPUT_CHARS = 2000


def _truncate_tool_messages(messages):
    trimmed = []
    for m in messages:
        if isinstance(m, ToolMessage) and isinstance(m.content, str) and len(m.content) > MAX_TOOL_OUTPUT_CHARS:
            m.content = m.content[:MAX_TOOL_OUTPUT_CHARS] + "\n... [output truncated]"
        trimmed.append(m)
    return trimmed


# ── LLM ───────────────────────────────────────
# kimi-k3 brain via TokenRouter's OpenAI-compatible API (LangChain stack)
llm = ChatOpenAI(
    model=Config.KIMI_MODEL,
    api_key=Config.KIMI_API_KEY,
    base_url=Config.KIMI_BASE_URL,
)
llm_with_tools = llm.bind_tools(tools_list)

# ── Agent Node ─────────────────────────────────
def agent(state: MessagesState):
    trimmed_history = trimmer.invoke(state["messages"])
    return {"messages": [llm_with_tools.invoke([SystemMessage(content=prompt1)] + trimmed_history)]}

#help to save convestion history in memory, you can customize it to save to a database or file system as needed
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
try:
    # Checkpointer
    checkpointer = SqliteSaver(conn=conn)
except Exception:
    conn.close()
    raise

# ── Graph ──────────────────────────────────────
graph = StateGraph(MessagesState)
graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools_list))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_edge("tools", "agent")


# Wrap the compiled graph so tool outputs are truncated before checkpointing.
_compiled_graph = graph.compile(checkpointer=checkpointer)


class _TruncatingWorkflow:
    """Thin wrapper that trims oversized tool outputs from the input messages
    before delegating to the compiled LangGraph workflow."""

    def __init__(self, workflow):
        self._workflow = workflow

    def _clean(self, payload):
        msgs = payload.get("messages")
        if msgs:
            payload["messages"] = _truncate_tool_messages(msgs)
        return payload

    def invoke(self, payload, config=None, **kwargs):
        return self._workflow.invoke(self._clean(payload), config, **kwargs)

    def stream(self, payload, config=None, **kwargs):
        return self._workflow.stream(self._clean(payload), config, **kwargs)

    def ainvoke(self, payload, config=None, **kwargs):
        return self._workflow.ainvoke(self._clean(payload), config, **kwargs)

    def astream(self, payload, config=None, **kwargs):
        return self._workflow.astream(self._clean(payload), config, **kwargs)

    def __getattr__(self, name):
        return getattr(self._workflow, name)


chat_workflow = _TruncatingWorkflow(_compiled_graph)

# ── Main Loop ──────────────────────────────────
if __name__ == "__main__":
    configs = {"configurable": {"thread_id": "rahul_session"}}
    print("Chatbot is ready. Type 'quit' to exit.")
    try:
        while True:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "quit":
                break
            result = chat_workflow.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                configs
            )
            print(f"\nAgent: {result['messages'][-1].content}")
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
