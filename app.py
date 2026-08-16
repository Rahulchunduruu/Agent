import json
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import HumanMessage
from main import chat_workflow

LIGHT_CSS = '<style> html { --background-color:#ffffff; --secondary-background-color:#f0f2f6; --text-color:#262730; --primary-color:#ff4b4b; } [data-testid=stAppViewContainer]{background-color:#ffffff;} [data-testid=stSidebar]{background-color:#f0f2f6;} [data-testid=stSidebar]>div{background-color:#f0f2f6;} [data-testid=stChatMessage]{background-color:#f0f2f6; color:#262730;} [data-testid=stChatInput] textarea{background-color:#ffffff; color:#262730;} [data-testid=stMarkdownContainer]{color:#262730;} h1,h2,h3,h4,h5,h6{color:#262730;} </style>'

DARK_CSS = '<style> html { --background-color:#0e1117; --secondary-background-color:#262730; --text-color:#fafafa; --primary-color:#ff4b4b; } [data-testid=stAppViewContainer]{background-color:#0e1117;} [data-testid=stSidebar]{background-color:#0e1117;} [data-testid=stSidebar]>div{background-color:#0e1117;} [data-testid=stChatMessage]{background-color:#262730; color:#fafafa;} [data-testid=stChatInput] textarea{background-color:#0e1117; color:#fafafa;} [data-testid=stMarkdownContainer]{color:#fafafa;} h1,h2,h3,h4,h5,h6{color:#fafafa;} </style>'

def apply_theme(theme):
    css = LIGHT_CSS if theme == 'light' else DARK_CSS
    st.markdown(css, unsafe_allow_html=True)


def copy_button(text, theme="dark"):
    """Renders a compact copy-to-clipboard button below an AI message."""
    escaped = json.dumps(text)
    if theme == "light":
        bg, fg, border = "#ffffff", "#262730", "#c9c9c9"
    else:
        bg, fg, border = "#0e1117", "#fafafa", "#3f4451"
    html = (
        '<button id="copyBtn" style="background:' + bg + '; color:' + fg +
        '; border:1px solid ' + border + '; border-radius:6px; padding:3px 10px;'
        ' font-size:12px; cursor:pointer; font-family:sans-serif;">📋 Copy</button>'
        '<script>'
        'var text = ' + escaped + ';'
        'var btn = document.getElementById("copyBtn");'
        'function showDone(){ btn.innerHTML = "✅ Copied!"; setTimeout(function(){ btn.innerHTML = "📋 Copy"; }, 1500); }'
        'function fallback(){ var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.focus(); ta.select(); try { document.execCommand("copy"); showDone(); } catch(e) { btn.innerHTML = "❌ Failed"; } document.body.removeChild(ta); }'
        'btn.addEventListener("click", function(){'
        ' if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(showDone).catch(fallback); }'
        ' else { fallback(); }'
        '});'
        '</script>'
    )
    components.html(html, height=36)



st.set_page_config(page_title="AI Agent Bot", page_icon="🤖", layout="wide")
st.title("🤖 AI Agent Bot")

if chat_workflow is None:
    st.error("Unable to start the AI agent workflow.")
    st.stop()

THREAD_ID = "streamlit_session"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "retry_requested" not in st.session_state:
    st.session_state.retry_requested = False
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

apply_theme(st.session_state.theme)

with st.sidebar:
    st.header("⚙️ Panel")
    theme_label = "☀️ Light Mode" if st.session_state.theme == "dark" else "🌙 Dark Mode"
    if st.button(theme_label, key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.divider()
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.retry_requested = False
        st.rerun()
    st.divider()
    st.caption("🤖 Powered by Rahul")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("error"):
            st.error(msg["content"])
        else:
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                copy_button(msg["content"], st.session_state.theme)


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


def run_agent_turn(user_input):
    full_reply = ""
    text_placeholder = None
    tool_calls_shown = set()
    had_error = False

    try:
        for chunk, metadata in chat_workflow.stream(
            {"messages": [HumanMessage(content=user_input)]},
            {"configurable": {"thread_id": THREAD_ID}},
            stream_mode="messages",
        ):
            node = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""

            tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
            if node == "agent" and tool_call_chunks:
                for tc in tool_call_chunks:
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    if name and name not in tool_calls_shown:
                        tool_calls_shown.add(name)
                        with st.expander("🔧 Calling tool: " + str(name)):
                            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)
                            if isinstance(args, dict) and args:
                                st.json(args)
                            else:
                                st.caption("Running...")

            if getattr(chunk, "type", "") == "tool":
                tool_name = getattr(chunk, "name", "tool") or "tool"
                result_text = extract_text(getattr(chunk, "content", ""))
                with st.expander("📥 Result from " + str(tool_name)):
                    st.code(result_text[:1500], language=None)

            if node == "agent":
                content = getattr(chunk, "content", "")
                if isinstance(content, list):
                    content = extract_text(content)
                if isinstance(content, str) and content:
                    if text_placeholder is None:
                        text_placeholder = st.empty()
                    full_reply += content
                    text_placeholder.markdown(full_reply + "▌")

        if full_reply.strip():
            reply = full_reply.strip()
            if text_placeholder is not None:
                text_placeholder.markdown(full_reply)
            else:
                st.markdown(full_reply)
        else:
            reply = "No response received."
            had_error = True
            if text_placeholder is not None:
                text_placeholder.error(reply)
            else:
                st.error(reply)

    except Exception as e:
        had_error = True
        reply = "Error generating response: {}".format(e)
        if text_placeholder is not None:
            text_placeholder.error(reply)
        else:
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply, "error": had_error})
    if not had_error:
        copy_button(reply, st.session_state.theme)
    return reply, had_error


def render_retry_button(key):
    if st.button("🔄 Retry last request", key=key):
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            st.session_state.messages.pop()
        st.session_state.retry_requested = True
        st.rerun()


user_input = st.chat_input("Ask your AI agent anything...")

last_is_error = (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "assistant"
    and st.session_state.messages[-1].get("error")
)
if not user_input and last_is_error and not st.session_state.retry_requested:
    render_retry_button("retry_btn_persist")

if user_input:
    st.session_state.retry_requested = False
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        reply, had_error = run_agent_turn(user_input)

    if had_error:
        render_retry_button("retry_btn")

elif st.session_state.retry_requested:
    st.session_state.retry_requested = False

    last_user = next(
        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
        None,
    )

    if last_user is not None:
        with st.chat_message("assistant"):
            st.caption("🔄 Retrying your last request...")
            reply, had_error = run_agent_turn(last_user)
        if had_error:
            render_retry_button("retry_btn")
    else:
        st.warning("Nothing to retry — the conversation is empty.")
