"""Streamlit view for the banking assistant."""

from __future__ import annotations

import streamlit as st
from tenacity import RetryError

from controllers.banking_controller import handle_banking_request
from models.banking_model import create_database


def render() -> None:
    st.set_page_config(page_title="CrewBank Assistant", page_icon="$", layout="centered")
    create_database()
    st.title("CrewBank Assistant")
    st.caption("CrewAI banking assistant with simulated MCP database tools")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello. Ask about your account, transactions, spending, or a service request.",
        }]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a banking question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Checking the appropriate banking specialist..."):
                try:
                    response = handle_banking_request(prompt)
                except RetryError:
                    response = "The model or a banking tool is rate-limited. Please try again shortly."
                except Exception as error:
                    text = str(error)
                    if "429" in text or "rate limit" in text.lower() or "too many requests" in text.lower():
                        response = "The model is rate-limited. Please try again shortly."
                    else:
                        response = f"I could not complete that request: {text}"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
