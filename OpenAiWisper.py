# .streamlit/secrets.toml
OPENAI_API_KEY = "YOUR_API_KEY"

import streamlit as st
from openai import OpenAI


st.title("Whisper Endpoint")

# Set Model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "whisper-1"
client = OpenAI(api_key = st.secrets(OPENAI_API_KEY))

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Insert Recording",accept_file=True,file_type="webm"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

with st.chat_message("assistant"):
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file= [{"role": m["role"], "content": m["content"]}
           for m in st.session_state.messages],
    transcription=True
)
response = st.write_stream(transcription.text)
st.session_state.messages.append({"role": "assistant", "content": response})
