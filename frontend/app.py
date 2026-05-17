import streamlit as st
import requests

st.set_page_config(
    page_title="DocuMind AI Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = "http://127.0.0.1:8000/api"

st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .stChatMessage { border-radius: 12px; margin-bottom: 10px; padding: 15px; }
        h1 { font-weight: 800 !important; color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_file_id" not in st.session_state:
    st.session_state.active_file_id = "No Active Document"

with st.sidebar:
    st.title("📁 Document Portal")
    st.markdown("Upload any PDF from your PC or Mobile device to securely stream it to your cloud isolation segment.")
    st.write("---")
    
    # Premium Native File Browser Component 🎯
    uploaded_file = st.file_uploader("Choose a PDF document:", type=["pdf"])
    
    if st.button("🚀 Process & Sync Document", use_container_width=True):
        if uploaded_file is None:
            st.warning("Please upload a valid PDF file first.")
        else:
            with st.spinner("Streaming file bytes and indexing cloud vectors..."):
                try:
                    # Format payload as standard multipart/form-data binary structure
                    files_payload = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
                    }
                    
                    response = requests.post(f"{BACKEND_URL}/ingest", files=files_payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        server_file_id = data.get("file_id")
                        
                        # Dynamically switch workspace partition
                        st.session_state.active_file_id = server_file_id
                        st.session_state.messages = [] # Flush view history for clean slate
                        
                        st.success(f"Deployed safely to segment: '{server_file_id}'")
                        st.rerun()
                    else:
                        st.error(f"Ingestion Failed: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Could not reach Backend server: {e}")
                    
    st.write("---")
    if st.button("🗑️ Clear Current Chat Screen", use_container_width=True):
        st.session_state.messages = []
        st.success("Screen history wiped.")
        st.rerun()

st.title("🧠 DocuMind AI Corporate")
st.markdown(f"Active Secure Sandbox Segment: `{st.session_state.active_file_id}`")
st.write("---")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_query := st.chat_input("Ask a question about your active document context..."):
    if st.session_state.active_file_id == "No Active Document":
        st.error("Please upload and process a document in the sidebar before asking questions.")
    else:
        with st.chat_message("user"):
            st.markdown(user_query)
            
        formatted_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        chat_payload = {
            "question": user_query,
            "file_id": st.session_state.active_file_id,
            "history": formatted_history
        }
        
        st.session_state.messages.append({"role": "user", "content": user_query})
            
        with st.chat_message("assistant"):
            with st.spinner("Searching segregated partition vectors..."):
                try:
                    response = requests.post(f"{BACKEND_URL}/chat", json=chat_payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_answer = data.get("answer")
                        score = data.get("confidence_score")
                        
                        full_payload = f"{ai_answer}\n\n`📊 Match Confidence: {score}%`"
                        st.markdown(full_payload)
                        st.session_state.messages.append({"role": "assistant", "content": full_payload})
                    else:
                        st.error(response.json().get("detail", "Error processing request."))
                except Exception as e:
                    st.error(f"Failed to communicate with FastAPI Backend: {e}")