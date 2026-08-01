import streamlit as st
from langchain_core.messages import HumanMessage
from main import chat_workflow

st.set_page_config(page_title="AI Agent Bot", page_icon="🤖")
st.title("🤖 AI Agent Bot")

if chat_workflow is None:
    st.error("Unable to start the AI agent workflow.")
    st.stop()

THREAD_ID = "streamlit_session"

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def extract_text(content):
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                text_parts.append(part.get("text", ""))
            else:
                text_parts.append(str(part))
        return "".join(text_parts)
    if isinstance(content, str):
        return content
    return str(content or "")


user_input = st.chat_input("Ask your AI agent anything...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                state = chat_workflow.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    {"configurable": {"thread_id": THREAD_ID}},
                )
                messages = state.get("messages", [])
                reply = ""
                for msg in reversed(messages):
                    content = getattr(msg, "content", "")
                    if isinstance(content, list):
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict):
                                text_parts.append(part.get("text", ""))
                            else:
                                text_parts.append(str(part))
                        content = "".join(text_parts)
                    if isinstance(content, str) and content.strip():
                        if getattr(msg, "type", "") == "ai":
                            reply = content.strip()
                            break
                reply = reply or "No response received."
            except Exception as e:
                reply = "Error generating response: {}".format(e)

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})