"""
Streamlit Chat Interface for Scam Honeypot Demo
Users can interact with the system as scammers and see real-time intelligence extraction
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import Dict, List
import time

# Page configuration
st.set_page_config(
    page_title="🕷️ Scam Honeypot Demo",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        animation: fadeIn 0.3s;
    }
    .user-message {
        background-color: #1976d2;
        border-left: 4px solid #0d47a1;
        color: white;
    }
    .agent-message {
        background-color: #7b1fa2;
        border-left: 4px solid #4a148c;
        color: white;
    }
    .intelligence-box {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
    }
    .scam-alert {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    .stats-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Backend configuration
# Uses environment variable for production, falls back to localhost for development
UI_BACKEND_URL = os.getenv("UI_BACKEND_URL", "http://localhost:8001")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "intelligence" not in st.session_state:
    st.session_state.intelligence = {
        "bankAccounts": [],
        "upiIds": [],
        "phoneNumbers": [],
        "phishingLinks": [],
        "suspiciousKeywords": []
    }
if "scam_detected" not in st.session_state:
    st.session_state.scam_detected = False
if "scam_type" not in st.session_state:
    st.session_state.scam_type = None
if "confidence" not in st.session_state:
    st.session_state.confidence = 0.0
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False

# Header
st.markdown("""
    <div class="main-header">
        <h1>🕷️ Agentic Honey-Pot Demo</h1>
        <p>AI-powered Scam Detection & Intelligence Extraction</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    api_key_input = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your API key to authenticate",
        placeholder="team_recursives"
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.api_key_valid = False
    
    # Validate API key button
    if st.button("🔑 Connect", use_container_width=True):
        if api_key_input:
            try:
                # Try to create a new session to validate key
                response = requests.post(
                    f"{UI_BACKEND_URL}/session/new",
                    headers={"x-api-key": api_key_input},
                    timeout=5
                )
                if response.status_code == 200:
                    st.session_state.api_key_valid = True
                    st.session_state.session_id = response.json()["session_id"]
                    st.success("✅ Connected successfully!")
                    st.rerun()
                else:
                    st.error("❌ Invalid API key")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
        else:
            st.warning("Please enter an API key")
    
    # Connection status
    if st.session_state.api_key_valid:
        st.success("🟢 Connected")
    else:
        st.warning("🔴 Not Connected")
    
    st.divider()
    
    # Session management
    st.header("📊 Session Info")
    
    if st.session_state.session_id:
        st.text_input("Session ID", value=st.session_state.session_id, disabled=True)
        
        # Session stats
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="stats-box">
                    <h3>{st.session_state.message_count}</h3>
                    <p>Messages</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            scam_status = "🚨 Scam" if st.session_state.scam_detected else "✅ Clean"
            st.markdown(f"""
                <div class="stats-box">
                    <h3>{scam_status}</h3>
                    <p>Status</p>
                </div>
            """, unsafe_allow_html=True)
        
        # New session button
        if st.button("🔄 New Session", use_container_width=True):
            try:
                response = requests.post(
                    f"{UI_BACKEND_URL}/session/new",
                    headers={"x-api-key": st.session_state.api_key},
                    timeout=5
                )
                if response.status_code == 200:
                    st.session_state.session_id = response.json()["session_id"]
                    st.session_state.messages = []
                    st.session_state.intelligence = {
                        "bankAccounts": [],
                        "upiIds": [],
                        "phoneNumbers": [],
                        "phishingLinks": [],
                        "suspiciousKeywords": []
                    }
                    st.session_state.scam_detected = False
                    st.session_state.scam_type = None
                    st.session_state.confidence = 0.0
                    st.session_state.message_count = 0
                    st.success("New session created!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error creating session: {str(e)}")
    
    st.divider()
    
    # Help section
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **Step 1:** Enter your API key above and click Connect
        
        **Step 2:** Type messages as if you're a scammer
        - Try: "Your account is blocked! Send OTP to verify"
        - Try: "Congratulations! You won ₹50,000. Share account number"
        - Try: "Call +91-9876543210 for KYC update"
        
        **Step 3:** Watch the AI agent respond naturally
        
        **Step 4:** See intelligence extracted in real-time
        """)
    
    with st.expander("🔧 Backend Status"):
        try:
            response = requests.get(f"{UI_BACKEND_URL}/health", timeout=3)
            if response.status_code == 200:
                health = response.json()
                st.json(health)
        except:
            st.error("Backend not reachable")

# Main content area
if not st.session_state.api_key_valid:
    # Show welcome message if not connected
    st.info("👈 Please enter your API key in the sidebar to get started")
    
    st.markdown("""
    ### 🎯 What is this?
    
    This is a demo interface for the **Agentic Honey-Pot System** - an AI-powered tool that:
    
    - 🔍 **Detects scam intent** automatically
    - 🤖 **Engages scammers** with human-like responses
    - 📊 **Extracts intelligence** (bank accounts, UPI IDs, phone numbers, phishing links)
    - 🚨 **Never reveals detection** - maintains natural conversation
    
    ### 🚀 Try it yourself!
    
    Act as a scammer and see how the AI agent responds while secretly extracting information.
    
    ### Example Scam Messages:
    
    ```
    "Your account will be blocked! Click here to verify: http://phishing.com"
    "Congratulations! You won ₹1 lakh. Send your bank account number"
    "This is from SBI bank. Your KYC is incomplete. Share Aadhaar OTP"
    ```
    """)
    
else:
    # Chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat with Honeypot Agent")
        
        # Chat container
        chat_container = st.container(height=500)
        
        with chat_container:
            if not st.session_state.messages:
                st.info("👋 Start the conversation! The AI agent will respond as a potential victim.")
            
            # Display messages
            for msg in st.session_state.messages:
                if msg["sender"] == "scammer":
                    st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>You (Scammer):</strong><br>
                            {msg['text']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="chat-message agent-message">
                            <strong>🤖 Honeypot Agent:</strong><br>
                            {msg['text']}
                        </div>
                    """, unsafe_allow_html=True)
        
        # Message input
        with st.form(key="message_form", clear_on_submit=True):
            user_input = st.text_input(
                "Your message:",
                placeholder="Type your message here...",
                label_visibility="collapsed"
            )
            
            col_send, col_example = st.columns([1, 2])
            
            with col_send:
                send_button = st.form_submit_button("📤 Send", use_container_width=True)
            
            with col_example:
                if st.form_submit_button("💡 Try Example", use_container_width=True):
                    examples = [
                        "Your account is blocked! Click here to unblock: http://fake-bank.com",
                        "Congratulations! You won ₹50,000 in lottery. Share your bank account",
                        "This is SBI customer care. Your card is suspended. Send OTP to verify",
                        "Call +91-9876543210 immediately for account KYC update"
                    ]
                    import random
                    user_input = random.choice(examples)
                    send_button = True
        
        # Handle message sending
        if send_button and user_input:
            with st.spinner("🤔 Agent is thinking..."):
                try:
                    # Send message to backend
                    response = requests.post(
                        f"{UI_BACKEND_URL}/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "message": user_input,
                            "api_key": st.session_state.api_key
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Update messages
                        st.session_state.messages.append({
                            "sender": "scammer",
                            "text": user_input
                        })
                        st.session_state.messages.append({
                            "sender": "agent",
                            "text": data["agent_reply"]
                        })
                        
                        # Update intelligence
                        st.session_state.intelligence = data["intelligence"]
                        st.session_state.scam_detected = data["scam_detected"]
                        st.session_state.scam_type = data.get("scam_type")
                        st.session_state.confidence = data.get("confidence", 0.0)
                        st.session_state.message_count = data["message_count"]
                        
                        st.rerun()
                    else:
                        st.error(f"Error: {response.status_code}")
                
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. The main honeypot service might be slow.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.header("📊 Intelligence")
        
        # Scam detection alert
        if st.session_state.scam_detected:
            st.markdown(f"""
                <div class="scam-alert">
                    <h3>🚨 Scam Detected!</h3>
                    <p><strong>Type:</strong> {st.session_state.scam_type or 'unknown'}</p>
                    <p><strong>Confidence:</strong> {st.session_state.confidence:.0%}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No scam detected yet")
        
        st.divider()
        
        # Intelligence display
        intel = st.session_state.intelligence
        
        # Bank accounts
        with st.expander(f"🏦 Bank Accounts ({len(intel.get('bankAccounts', []))})", expanded=True):
            if intel.get("bankAccounts"):
                for acc in intel["bankAccounts"]:
                    st.code(acc)
            else:
                st.text("None detected")
        
        # UPI IDs
        with st.expander(f"💳 UPI IDs ({len(intel.get('upiIds', []))})", expanded=True):
            if intel.get("upiIds"):
                for upi in intel["upiIds"]:
                    st.code(upi)
            else:
                st.text("None detected")
        
        # Phone numbers
        with st.expander(f"📞 Phone Numbers ({len(intel.get('phoneNumbers', []))})", expanded=True):
            if intel.get("phoneNumbers"):
                for phone in intel["phoneNumbers"]:
                    st.code(phone)
            else:
                st.text("None detected")
        
        # Phishing links
        with st.expander(f"🔗 Phishing Links ({len(intel.get('phishingLinks', []))})", expanded=True):
            if intel.get("phishingLinks"):
                for link in intel["phishingLinks"]:
                    st.code(link)
            else:
                st.text("None detected")
        
        # Suspicious keywords
        with st.expander(f"🔑 Suspicious Keywords ({len(intel.get('suspiciousKeywords', []))})", expanded=True):
            if intel.get("suspiciousKeywords"):
                st.write(", ".join(intel["suspiciousKeywords"]))
            else:
                st.text("None detected")
        
        st.divider()
        
        # Download intelligence
        if st.button("💾 Export Intelligence", use_container_width=True):
            export_data = {
                "session_id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "scam_detected": st.session_state.scam_detected,
                "scam_type": st.session_state.scam_type,
                "confidence": st.session_state.confidence,
                "intelligence": st.session_state.intelligence,
                "messages": st.session_state.messages
            }
            
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"intelligence_{st.session_state.session_id}.json",
                mime="application/json"
            )

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🕷️ Agentic Honey-Pot Demo | Built with Streamlit | <a href="https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com" target="_blank">Main System</a></p>
    </div>
""", unsafe_allow_html=True)
