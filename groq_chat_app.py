import streamlit as st
import os
from groq import Groq, APIError, RateLimitError # Import specific errors

# --- Page Configuration ---
st.set_page_config(
    page_title="Groq Chat",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Sidebar Setup ---
st.sidebar.title("Groq Chat Settings ⚡")
st.sidebar.markdown("Enter your Groq API Key and select a model.")

# Get Groq API Key
# Use environment variable if available, otherwise use text input
default_api_key = os.environ.get("GROQ_API_KEY", "")
groq_api_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    value=default_api_key,
    help="Get your API key from https://console.groq.com/keys"
)

if not groq_api_key and not default_api_key:
    st.sidebar.warning("Please enter your Groq API Key to start chatting.")
elif not groq_api_key and default_api_key:
    st.sidebar.info("Using API Key from environment variable.")
    groq_api_key = default_api_key # Ensure it's set for the client

# Model Selection
available_models = [
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-llama-70b",
    "gemma2-9b-it",
]
selected_model = st.sidebar.selectbox(
    "Choose a Groq Model",
    options=available_models,
    index=0 # Default to the first model
)

# Clear Chat Button
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun() # Rerun the app to reflect the cleared state

# --- Main Chat Interface ---
st.title("💬 Groq Chatbot")
st.caption(f"Using model: {selected_model}")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat messages
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "⚡"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- Chat Input and Response Logic ---
if prompt := st.chat_input("What can I help you with today?"):
    if not groq_api_key:
        st.warning("Please enter your Groq API Key in the sidebar first!")
        st.stop() # Stop execution if no API key

    # Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Prepare messages for Groq API (ensure correct format)
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # Display assistant response placeholder and stream response
    with st.chat_message("assistant", avatar="⚡"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # Initialize Groq client (do this only when needed)
            client = Groq(api_key=groq_api_key)

            # --- Streaming API Call ---
            stream = client.chat.completions.create(
                model=selected_model,
                messages=api_messages,
                stream=True,
            )

            for chunk in stream:
                chunk_content = chunk.choices[0].delta.content
                if chunk_content is not None:
                    full_response += chunk_content
                    message_placeholder.markdown(full_response + "▌") # Add cursor effect

            message_placeholder.markdown(full_response) # Display final response

        except APIError as e:
            st.error(f"Groq API Error: {e}")
            full_response = f"Error: {e}" # Store error in history for context
        except RateLimitError:
            st.error("Rate limit exceeded. Please try again later.")
            full_response = "Error: Rate limit exceeded."
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            full_response = f"Error: {e}"

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add a small footer or instruction if the chat is empty
if not st.session_state.messages:
    st.info("Enter a message in the box below to start the chat!")