import streamlit as st
from project.sql_agents.sql_agent_with_rag import db_agent
from langchain_core.messages import HumanMessage

CONFIG = {"configurable":{"thread_id":"thread-1"}}

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

# message_history = []
user_input = st.chat_input("Type here")

# loading the conversation history
for message in  st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

if user_input:

    st.session_state["message_history"].append({"role":"User","content":user_input})
    with st.chat_message("User"):
        st.text(user_input)
    
    with st.chat_message("Assistant"):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in db_agent.stream(
                {"messages":[HumanMessage(content=user_input)]},
                config={"configurable":{"thread_id":"thread_id-1"}},
                stream_mode="messages"))
    
    st.session_state["message_history"].append({"role":"Assistant","content":ai_message})