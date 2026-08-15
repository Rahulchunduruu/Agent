from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from config import Config
from tools import tools_list
from prompt import prompt1
import sqlite3
import os

os.environ["USER_AGENT"] = "MyAgent/1.0"
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
    return {"messages": [llm_with_tools.invoke([SystemMessage(content=prompt1)] + state["messages"])]}

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




chat_workflow = graph.compile(checkpointer=checkpointer)

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