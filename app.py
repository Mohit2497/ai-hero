"""
Modern Streamlit app for Microsoft AI Agents Documentation Assistant
with Gemini API rate limiting, conversation context, small talk handling, and enhanced UI.
"""

import streamlit as st
import asyncio
import os
import time
import json
from datetime import datetime
from pathlib import Path
import logging

from app import ingest, search_agent, logs

logger = logging.getLogger(__name__)

# ============================================================================#
# CONFIGURATION
# ============================================================================#

RATE_LIMIT_FILE = Path("rate_limit_state.json")
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_DAY = 1500
MAX_TOKENS_PER_MINUTE = 1000000
REQUEST_COOLDOWN = 6.0  # seconds

# ============================================================================#
# RATE LIMITER CLASS
# ============================================================================#

class RateLimiter:
    def __init__(self):
        self.load_state()
        self.request_timestamps = []

    def load_state(self):
        if RATE_LIMIT_FILE.exists():
            try:
                with open(RATE_LIMIT_FILE, 'r') as f:
                    state = json.load(f)
                    self.minute_requests = [float(t) for t in state.get('minute_requests', [])]
                    self.daily_requests = [float(t) for t in state.get('daily_requests', [])]
                    self.last_request_time = state.get('last_request_time', 0)
            except Exception:
                self.reset_state()
        else:
            self.reset_state()

    def reset_state(self):
        self.minute_requests = []
        self.daily_requests = []
        self.last_request_time = 0
        self.request_timestamps = []

    def save_state(self):
        state = {
            'minute_requests': self.minute_requests,
            'daily_requests': self.daily_requests,
            'last_request_time': self.last_request_time
        }
        try:
            with open(RATE_LIMIT_FILE, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving rate limit state: {e}")

    def clean_old_requests(self):
        current_time = time.time()
        self.minute_requests = [t for t in self.minute_requests if t > current_time - 60]
        self.daily_requests = [t for t in self.daily_requests if t > current_time - 86400]
        self.request_timestamps = [t for t in self.request_timestamps if t > current_time - 300]

    def calculate_backoff_time(self):
        if len(self.request_timestamps) >= 3:
            recent_requests = [t for t in self.request_timestamps if t > time.time() - 60]
            if len(recent_requests) >= 3:
                return min(2 ** (len(recent_requests) - 2), 60)
        return 0

    def can_make_request(self):
        self.clean_old_requests()
        current_time = time.time()

        if len(self.minute_requests) >= MAX_REQUESTS_PER_MINUTE:
            oldest_request = min(self.minute_requests)
            wait_time = 60 - (current_time - oldest_request)
            return False, f"⚠️ Minute limit exceeded. Wait {wait_time:.0f}s."

        if len(self.daily_requests) >= MAX_REQUESTS_PER_DAY:
            return False, "⚠️ Daily limit reached. Resets at midnight PT."

        if self.last_request_time > 0:
            elapsed = current_time - self.last_request_time
            cooldown = REQUEST_COOLDOWN + self.calculate_backoff_time()
            if elapsed < cooldown:
                return False, f"⏳ Please wait {cooldown - elapsed:.1f}s before next request."

        return True, None

    def record_request(self):
        current_time = time.time()
        self.minute_requests.append(current_time)
        self.daily_requests.append(current_time)
        self.request_timestamps.append(current_time)
        self.last_request_time = current_time
        self.save_state()

    def get_stats(self):
        self.clean_old_requests()
        current_time = time.time()
        minute_remaining = MAX_REQUESTS_PER_MINUTE - len(self.minute_requests)
        daily_remaining = MAX_REQUESTS_PER_DAY - len(self.daily_requests)
        return {
            'minute_used': len(self.minute_requests),
            'minute_limit': MAX_REQUESTS_PER_MINUTE,
            'minute_remaining': minute_remaining,
            'daily_used': len(self.daily_requests),
            'daily_limit': MAX_REQUESTS_PER_DAY,
            'daily_remaining': daily_remaining,
            'tokens_per_minute': MAX_TOKENS_PER_MINUTE
        }

# ============================================================================#
# CACHE RESOURCES
# ============================================================================#

@st.cache_resource
def get_rate_limiter():
    return RateLimiter()

@st.cache_resource
def load_agent(repo_owner: str, repo_name: str):
    cache_file = Path(__file__).parent / "data" / "ms_ai_agents_index.pkl"

    if cache_file.exists():
        logger.info("Loading pre-built index from cache...")
        index = ingest.index_data(repo_owner, repo_name, use_cache=True, cache_filepath=str(cache_file))
    else:
        logger.info("Building fresh index...")
        index = ingest.index_data(repo_owner, repo_name, chunk=True, chunking_params={'size': 2000, 'step': 1000}, use_cache=False)

    agent = search_agent.init_agent(index, repo_owner, repo_name)
    return agent

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

async def get_agent_response(agent, user_prompt: str):
    response = await agent.run(user_prompt=user_prompt)
    return response.output if hasattr(response, "output") else str(response)

# ============================================================================#
# STREAMLIT PAGE SETUP
# ============================================================================#

st.set_page_config(page_title="AI Agents Assistant", page_icon="🎓", layout="wide")
st.markdown("""
<style>
.chat-message.user { background: #DCF8C6; border-radius:15px; padding:10px; margin:5px 0; }
.chat-message.assistant { background: #E8EAF6; border-radius:15px; padding:10px; margin:5px 0; }
.sidebar .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Repo Assistant")
st.caption("Learn about AI agents using Microsoft's documentation.")

# Sidebar
st.sidebar.title("Settings & Info")
REPO_OWNER = st.sidebar.text_input("Repository Owner", "microsoft")
REPO_NAME = st.sidebar.text_input("Repository Name", "ai-agents-for-beginners")

rate_limiter = get_rate_limiter()
stats = rate_limiter.get_stats()

st.sidebar.markdown("### Rate Limit Status")
st.sidebar.progress(min(stats['minute_used'], stats['minute_limit']) / stats['minute_limit'])
st.sidebar.markdown(f"- Minute: {stats['minute_used']}/{stats['minute_limit']} used")
st.sidebar.markdown(f"- Daily: {stats['daily_used']}/{stats['daily_limit']} used")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []

if st.sidebar.button("Download Chat"):
    chat_json = json.dumps(st.session_state.messages, indent=2)
    st.sidebar.download_button("Download JSON", chat_json, file_name="chat.json")

# ============================================================================#
# INITIALIZE AGENT
# ============================================================================#

try:
    if "agent_loaded" not in st.session_state:
        with st.spinner("Initializing AI Assistant..."):
            agent = load_agent(REPO_OWNER, REPO_NAME)
            st.session_state.agent_loaded = True
    else:
        agent = load_agent(REPO_OWNER, REPO_NAME)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        role_icon = "🧑" if msg["role"] == "user" else "🤖"
        timestamp = msg.get("time", datetime.now().strftime("%H:%M"))
        with st.chat_message(msg["role"]):
            st.markdown(f"**{role_icon} [{timestamp}]**: {msg['content']}")

    # -------------------------------
    # Chat input (conversational + domain-specific)
    # -------------------------------

    def generate_response(user_text: str) -> str:
        """
        Decide if this is small talk or a domain question,
        and respond appropriately.
        """
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon"]
        farewells = ["bye", "goodbye", "see you", "later"]
        thanks = ["thanks", "thank you", "thx"]

        text_lower = user_text.strip().lower()

        if any(word in text_lower for word in greetings):
            return "🤖 Hi there! How can I help you with AI agents today?"
        elif any(word in text_lower for word in farewells):
            return "🤖 Goodbye! Feel free to ask more about AI agents anytime."
        elif any(word in text_lower for word in thanks):
            return "🤖 You're welcome! Do you have any more questions about AI agents?"
        else:
            return None  # signal to query AI agent

    if prompt := st.chat_input("Ask about AI agents, concepts, or implementations..."):

        # Check for small talk first
        response_output = generate_response(prompt)

        if response_output is None:
            # Domain-specific question: call the AI agent
            can_request, msg_status = rate_limiter.can_make_request()
            if not can_request:
                st.warning(msg_status)
                response_output = "⚠️ " + msg_status
            else:
                rate_limiter.record_request()

                # Use last 5 messages as context
                context = "\n".join(
                    [f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]]
                )

                conv_prompt = (
                    "Answer concisely and conversationally, staying on topic about AI agents.\n\n"
                    f"Context:\n{context}\n\nQuestion: {prompt}"
                )

                with st.spinner("🤔 Thinking..."):
                    response_output = run_async(get_agent_response(agent, conv_prompt))

        # Display user message
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "time": datetime.now().strftime("%H:%M")}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        st.session_state.messages.append(
            {"role": "assistant", "content": response_output, "time": datetime.now().strftime("%H:%M")}
        )
        with st.chat_message("assistant"):
            st.markdown(response_output)

        # Log interaction (optional)
        try:
            logs.log_interaction_to_file(
                agent,
                [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response_output},
                ],
            )
        except Exception as e:
            logger.error(f"Logging error: {e}")

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Please refresh the page or check the console for more details.")
