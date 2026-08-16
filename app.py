import json
import time
import streamlit as st
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
    st.iframe(html, height=36)


def feedback_buttons(index, current_feedback=None, theme="dark"):
    """Renders compact thumbs-up/thumbs-down feedback buttons below an AI message."""
    if current_feedback == "up":
        st.caption("👍 Thanks for your feedback! 🙏")
        return
    if current_feedback == "down":
        st.caption("👎 Thanks — we'll keep improving! 🙏")
        return
    col1, col2, _ = st.columns([0.55, 0.55, 8.9])
    if col1.button("👍", key="fb_up_{}".format(index), help="Good response"):
        st.session_state.messages[index]["feedback"] = "up"
        st.rerun()
    if col2.button("👎", key="fb_down_{}".format(index), help="Bad response"):
        st.session_state.messages[index]["feedback"] = "down"
        st.rerun()


# ---- Welcome screen with suggestion chips (shown when conversation is empty) ----
SUGGESTIONS = [
    "🌤️ What's the weather in Guntur?",
    "🔍 Search the latest AI news",
    "📂 List files in my project",
    "🧮 Calculate 15% of 2400",
    "📧 Check my recent emails",
    "🏏 Latest sports news",
]


def render_welcome_screen():
    """Shows a friendly greeting + clickable suggestion chips when the chat is empty."""
    st.markdown(
        """
        <div style="text-align:center; padding: 30px 0 8px;">
            <div style="font-size:52px;">👋</div>
            <h2 style="margin-bottom:4px;">How can I help you today?</h2>
            <p style="opacity:0.65; margin-top:0;">Pick a suggestion below or type your own question</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        if cols[i % 2].button(suggestion, key="sug_{}".format(i), use_container_width=True):
            st.session_state.pending_input = suggestion
            st.rerun()


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
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

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

for msg_index, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("error"):
            st.error(msg["content"])
        else:
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                copy_button(msg["content"], st.session_state.theme)
                feedback_buttons(msg_index, msg.get("feedback"), st.session_state.theme)

# Show welcome screen + suggestion chips when the conversation is empty
if not st.session_state.messages and not st.session_state.get("pending_input"):
    render_welcome_screen()


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


def _parse_args_nicely(args_raw):
    """Parse accumulated tool-call args (streamed JSON fragments) into a dict when possible."""
    if not args_raw:
        return None
    if isinstance(args_raw, (dict, list)):
        return args_raw
    try:
        return json.loads(args_raw)
    except Exception:
        return args_raw if str(args_raw).strip() else None


def run_agent_turn(user_input):
    full_reply = ""
    text_placeholder = None
    active_tools = {}      # key -> {"status": widget, "start": time, "name": str, "args": str}
    completed_keys = set()
    had_error = False

    def find_entry_for_result(tool_name, tool_call_id):
        """Match a ToolMessage back to its tool-call status widget."""
        if tool_call_id and tool_call_id in active_tools and tool_call_id not in completed_keys:
            return tool_call_id
        for key, entry in active_tools.items():
            if key not in completed_keys and entry.get("name") == tool_name:
                return key
        return None

    def close_stale_tools():
        """Mark any tool still showing as 'running' as failed (avoids stuck spinners)."""
        for key, entry in active_tools.items():
            if key not in completed_keys:
                completed_keys.add(key)
                try:
                    entry["status"].update(
                        label="⚠️ {} — no result received".format(entry.get("name") or "tool"),
                        state="error",
                        expanded=False,
                    )
                except Exception:
                    pass

    try:
        for chunk, metadata in chat_workflow.stream(
            {"messages": [HumanMessage(content=user_input)]},
            {"configurable": {"thread_id": THREAD_ID}},
            stream_mode="messages",
        ):
            node = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""

            # ---- Tool call started (args stream in as chunks) ----
            tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
            if node == "agent" and tool_call_chunks:
                for tc in tool_call_chunks:
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    index = tc.get("index") if isinstance(tc, dict) else getattr(tc, "index", None)
                    args_chunk = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)

                    if not name and not tc_id:
                        continue
                    key = tc_id or "{}_{}".format(name or "tool", index if index is not None else 0)

                    if key not in active_tools:
                        active_tools[key] = {
                            "status": st.status("🔧 Running: {}...".format(name or "tool"), expanded=False),
                            "start": time.time(),
                            "name": name,
                            "args": "",
                        }
                    entry = active_tools[key]
                    if name and not entry["name"]:
                        entry["name"] = name
                    if args_chunk:
                        entry["args"] += args_chunk if isinstance(args_chunk, str) else json.dumps(args_chunk)

            # ---- Tool result arrived -> complete the status widget ----
            if getattr(chunk, "type", "") == "tool":
                tool_name = getattr(chunk, "name", "tool") or "tool"
                tool_call_id = getattr(chunk, "tool_call_id", None)
                result_text = extract_text(getattr(chunk, "content", ""))

                key = find_entry_for_result(tool_name, tool_call_id)
                if key is not None:
                    entry = active_tools[key]
                    completed_keys.add(key)
                    elapsed = time.time() - entry["start"]
                    widget = entry["status"]

                    parsed_args = _parse_args_nicely(entry["args"])
                    with widget:
                        if parsed_args:
                            st.markdown("**Input:**")
                            if isinstance(parsed_args, (dict, list)):
                                st.json(parsed_args)
                            else:
                                st.code(str(parsed_args)[:800], language=None)
                        st.markdown("**Output:**")
                        st.code(result_text[:1500], language=None)
                    widget.update(
                        label="✅ {} — done in {:.1f}s".format(tool_name, elapsed),
                        state="complete",
                        expanded=False,
                    )
                else:
                    # Result with no matching call widget (safety fallback)
                    with st.status("✅ {}".format(tool_name), state="complete", expanded=False):
                        st.code(result_text[:1500], language=None)

            # ---- Assistant text streaming ----
            if node == "agent":
                content = getattr(chunk, "content", "")
                if isinstance(content, list):
                    content = extract_text(content)
                if isinstance(content, str) and content:
                    if text_placeholder is None:
                        text_placeholder = st.empty()
                    full_reply += content
                    text_placeholder.markdown(full_reply + "▌")

        close_stale_tools()

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
        close_stale_tools()
        had_error = True
        reply = "Error generating response: {}".format(e)
        if text_placeholder is not None:
            text_placeholder.error(reply)
        else:
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply, "error": had_error, "feedback": None})
    if not had_error:
        copy_button(reply, st.session_state.theme)
        feedback_buttons(len(st.session_state.messages) - 1, None, st.session_state.theme)
    return reply, had_error


def render_retry_button(key):
    if st.button("🔄 Retry last request", key=key):
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            st.session_state.messages.pop()
        st.session_state.retry_requested = True
        st.rerun()


user_input = st.chat_input("Ask your AI agent anything...")

# Pick up input from suggestion-chip clicks
if not user_input and st.session_state.get("pending_input"):
    user_input = st.session_state.pop("pending_input")

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
