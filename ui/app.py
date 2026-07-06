"""
Streamlit Chat Application (Phase 4)

Provides a web interface for the Mutual Fund FAQ Assistant.
Implements client-side rate limiting to respect Groq API constraints.
"""
import sys
import os
import time

# Ensure we can import from our local packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from retrieval.vector_store import VectorStore
from generation.generator import generate_response
from config.settings import (
    APP_TITLE, 
    DISCLAIMER_TEXT, 
    WELCOME_MESSAGE, 
    EXAMPLE_QUESTIONS
)

# Client-side rate limit enforcement (buffer below Groq's 30 RPM limit)
MAX_REQUESTS_PER_MINUTE = 20

@st.cache_resource
def get_vector_store():
    """Cache the VectorStore connection so it persists across re-renders."""
    return VectorStore()

def check_rate_limit() -> bool:
    """
    Enforces client-side Requests Per Minute (RPM) limits.
    Returns True if allowed, False if blocked.
    """
    current_time = time.time()
    
    if "query_times" not in st.session_state:
        st.session_state.query_times = []
        
    # Purge timestamps older than 60 seconds
    st.session_state.query_times = [
        t for t in st.session_state.query_times 
        if current_time - t < 60
    ]
    
    if len(st.session_state.query_times) >= MAX_REQUESTS_PER_MINUTE:
        return False
        
    # Add new request timestamp
    st.session_state.query_times.append(current_time)
    return True

def process_user_input(prompt: str, vector_store: VectorStore):
    """Handle the user's prompt submission and UI updates."""
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. Enforce local rate limits
    if not check_rate_limit():
        msg = "⏳ **Rate Limit Active**: You're asking questions too quickly. Please wait 60 seconds before asking another question to avoid hitting global API limits."
        st.session_state.messages.append({"role": "assistant", "content": msg})
        with st.chat_message("assistant"):
            st.markdown(msg)
        return

    # 3. Process with LLM via Orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Searching mutual fund data..."):
            response = generate_response(prompt, vector_store)
            st.markdown(response)
            
    # 4. Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    st.set_page_config(page_title="Mutual Fund FAQ", page_icon="🏦", layout="centered")
    
    # Top Disclaimer
    st.warning(DISCLAIMER_TEXT, icon="⚠️")
    
    st.title(APP_TITLE)
    
    vector_store = get_vector_store()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Show Quick Action Buttons if no questions asked yet
    if len(st.session_state.messages) == 1:
        st.write("")
        for example in EXAMPLE_QUESTIONS:
            if st.button(example, use_container_width=True):
                process_user_input(example, vector_store)
                st.rerun()

    # Chat Input Box
    if prompt := st.chat_input("Ask a factual question about an HDFC Mutual Fund..."):
        process_user_input(prompt, vector_store)


if __name__ == "__main__":
    main()
