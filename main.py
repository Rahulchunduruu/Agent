from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from config import Config
from tools import tools_list
from prompt import prompt1

# ── LLM ───────────────────────────────────────
llm = ChatGroq(model="openai/gpt-oss-120b", api_key=Config.Groq_api_key)
llm_with_tools = llm.bind_tools(tools_list)

# ── Agent Node ─────────────────────────────────
def agent(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([SystemMessage(content=prompt1)] + state["messages"])]}

# ── Graph ──────────────────────────────────────
graph = StateGraph(MessagesState)
graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools_list))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_edge("tools", "agent")

# ── Checkpointer (MemorySaver for local dev) ───
# To use Redis instead:
#   from langgraph.checkpoint.redis import RedisSaver
#   rest_host = Config.UPSTASH_REDIS_REST_URL.replace("https://", "")
#   redis_url = f"rediss://default:{Config.UPSTASH_REDIS_REST_TOKEN}@{rest_host}:6379"
#   with RedisSaver.from_conn_string(redis_url, connection_args={"ssl_cert_reqs": None}) as checkpointer:
#       checkpointer.setup()
#       app = graph.compile(checkpointer=checkpointer)

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

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
            result = app.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                configs
            )
            print(f"\nAgent: {result['messages'][-1].content}")
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")