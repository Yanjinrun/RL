import streamlit as st
import json
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Medical Dialogue Explorer")

# Load data
@st.cache_data
def load_data(filepath):
    conversations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            conversations.append(json.loads(line))
    return conversations

conversations = load_data("/home/yjr/rl-health-dialogue/user_simulator/dialogues/all_dialogues_assistant_thinking.jsonl")
# Sidebar for navigation
st.sidebar.header("Navigation")
conv_idx = st.sidebar.selectbox(
    "Select Conversation",
    range(len(conversations)),
    format_func=lambda x: f"{x+1}. {conversations[x].get('dialogue_id', 'No ID')}"
)

# Display current conversation
conv = conversations[conv_idx]

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("📋 Metadata")
    st.json({
        "ID": conv.get('dialogue_id'),
        "Patient": f"{conv.get('patient_gender', '')}, {conv.get('patient_age', '')}",
        "Turns": conv.get('metadata', {}).get('turns'),
        "Class": conv.get('class_annotation', {}).get('primary_class'),
        "Risk": conv.get('class_annotation', {}).get('risk_level')
    })
    
    # Display background info
    with st.expander("Background Story"):
        st.json(conv.get('background_story', {}))

with col2:
    st.subheader("💬 Conversation")
    
    for msg in conv.get('dialogue_history', []):
        role = msg.get('role', 'unknown')
        
        if role == 'user':
            st.markdown(f"**👤 Patient:** {msg.get('content', '')}")
            if 'thinking' in msg:
                st.caption(f"*💭 {msg['thinking']}*")
        elif role == 'assistant':
            st.markdown(f"**🤖 Caregiver:** {msg.get('content', '')}")
            if 'thinking' in msg:
                st.caption(f"*💭 {msg['thinking']}*")
        elif role == 'system':
            st.info(f"**⚙️ System:** {msg.get('content', '')}")
        
        st.markdown("---")