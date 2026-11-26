"""Streamlit frontend for the AI Sales Voice Agent - Continuous Call Mode."""

import streamlit as st
import requests
from datetime import datetime, timedelta
import os
import tempfile

st.set_page_config(
    page_title="TechStore AI Sales Agent",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .user-bubble {
        background: #DCF8C6;
        padding: 10px 15px;
        border-radius: 15px 15px 3px 15px;
        margin: 5px 0;
        max-width: 85%;
        margin-left: auto;
        color: #1a1a1a;
        font-size: 15px;
    }
    .agent-bubble {
        background: #F0F0F0;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 3px;
        margin: 5px 0;
        max-width: 85%;
        color: #1a1a1a;
        font-size: 15px;
    }
    .summary-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px 25px;
        border-left: 5px solid #1f77b4;
        margin: 10px 0;
        color: #1a1a1a !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .summary-card strong {
        color: #1a1a1a !important;
        font-size: 16px;
    }
    .summary-card p, .summary-card span {
        color: #2c2c2c !important;
        font-size: 14px;
        line-height: 1.6;
    }
    .metric-box {
        background: #ffffff;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #d0d0d0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .metric-box h3 {
        color: #1a1a1a !important;
        margin: 0 0 5px 0;
        font-size: 20px;
    }
    .metric-box p {
        color: #555555 !important;
        margin: 0;
        font-size: 13px;
    }
    .hot-badge { background: #ff4b4b; color: white !important; padding: 3px 10px; border-radius: 20px; font-size: 13px; }
    .warm-badge { background: #ffa500; color: white !important; padding: 3px 10px; border-radius: 20px; font-size: 13px; }
    .cold-badge { background: #4b9fff; color: white !important; padding: 3px 10px; border-radius: 20px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000/api"

# Session state
for key, val in {
    "conversation_history": [],
    "current_customer": None,
    "chat_messages": [],
    "call_active": False,
    "last_audio": None,
    "show_summary": False,
    "summary_data": None,
    "lead_result": None,
    "appointment_result": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


def get_api_response(endpoint, method="GET", data=None):
    try:
        url = f"{API_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            r = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            r = requests.put(url, json=data, headers=headers, timeout=30)
        return (r.json(), None) if r.status_code in [200, 201] else (None, r.text)
    except Exception as e:
        return None, str(e)


def process_voice_message(audio_data):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_data.getbuffer())
        path = f.name
    try:
        with open(path, "rb") as f:
            resp = requests.post(f"{API_URL}/transcribe", files={"file": f}, timeout=30)
        if resp.status_code != 200:
            st.error(f"Transcription error: {resp.text}")
            return False

        transcription = resp.json()["transcription"]
        st.session_state.chat_messages.append({"type": "user", "content": transcription})

        response, error = get_api_response("/chat", "POST", {
            "customer_id": st.session_state.current_customer["id"] if st.session_state.current_customer else None,
            "customer_name": st.session_state.current_customer["name"] if st.session_state.current_customer else "Guest",
            "message": transcription,
            "conversation_history": st.session_state.conversation_history
        })

        if error:
            st.session_state.chat_messages.append({"type": "assistant", "content": f"Error: {error}"})
            return False

        agent_response = response["response"]
        st.session_state.chat_messages.append({"type": "assistant", "content": agent_response})
        st.session_state.conversation_history.append([transcription, agent_response])

        try:
            tts = requests.post(f"{API_URL}/text-to-speech", json={"text": agent_response}, timeout=30)
            if tts.status_code == 200 and len(tts.content) > 50:
                st.session_state.last_audio = tts.content
        except:
            pass

        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False
    finally:
        if os.path.exists(path):
            os.remove(path)


def render_summary(summary_text, customer_name):
    """Parse and render summary as beautiful cards."""
    st.markdown("---")
    st.markdown(f"## 📋 Call Summary — {customer_name}")
    st.markdown(f"*Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}*")
    st.markdown("---")

    lines = summary_text.strip().split("\n")
    sections = {}
    current_section = None
    buffer = []
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class='metric-box'>
            <h3 style='color:#000000;'>💬 {num_turns}</h3>
            <p style='color:#000000;'>Exchanges</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='metric-box'>
            <h3 style='color:#000000;'>{sentiment_emoji} {sentiment}</h3>
            <p style='color:#000000;'>Sentiment</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        budget = sections.get("BUDGET MENTIONED", "Not mentioned")
        st.markdown(f"""<div class='metric-box'>
            <h3 style='color:#000000;'>💰</h3>
            <p style='color:#000000;'>{budget[:30]}</p>
        </div>""", unsafe_allow_html=True)
        sections[current_section] = "\n".join(buffer).strip()

    # Metrics row
    num_turns = len(st.session_state.conversation_history)
    sentiment = sections.get("SENTIMENT", "Neutral").strip()
    sentiment_emoji = "😊" if "Positive" in sentiment else "😐" if "Neutral" in sentiment else "😟"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class='metric-box'>
            <h3 style='color:#1a1a1a;'>💬 {num_turns}</h3>
            <p style='color:#555;'>Exchanges</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='metric-box'>
            <h3 style='color:#1a1a1a;'>{sentiment_emoji} {sentiment}</h3>
            <p style='color:#555;'>Sentiment</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        budget = sections.get("BUDGET MENTIONED", "Not mentioned")
        st.markdown(f"""<div class='metric-box'>
            <h3 style='color:#1a1a1a;'>💰</h3>
            <p style='color:#555;'>{budget[:30]}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Section cards
    section_map = {
        "OVERVIEW": ("📌", "Overview"),
        "CUSTOMER REQUIREMENTS": ("🎯", "Customer Requirements"),
        "PRODUCTS DISCUSSED": ("💻", "Products Discussed"),
        "CONVERSATION HIGHLIGHTS": ("💡", "Highlights"),
        "NEXT STEPS": ("🚀", "Next Steps"),
    }

    for key, (icon, label) in section_map.items():
        if key in sections and sections[key]:
            content = sections[key]
            st.markdown(f"""
            <div class='summary-card'>
                <strong style='color:black; font-size:16px;'>{icon} {label}</strong>
                <hr style='border:none; border-top:1px solid #e0e0e0; margin:10px 0;'>
                <p style='color:#2c2c2c; font-size:14px; line-height:1.7; margin:0;'>{content.replace(chr(10), '<br>')}</p>
            </div>
            """, unsafe_allow_html=True)


# ==================== MAIN UI ====================

if not st.session_state.call_active and not st.session_state.show_summary:

    st.markdown("# 🤖 TechStore AI Voice Agent")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 Select Customer")
        customers, _ = get_api_response("/customers")
        names = ["New Customer"] + [c["name"] for c in (customers or [])]
        selected = st.selectbox("Customer:", names, key="cust_select_start")

        if selected != "New Customer":
            st.session_state.current_customer = next(
                (c for c in customers if c["name"] == selected), None
            )
        else:
            st.session_state.current_customer = None
            new_name = st.text_input("Enter name:", key="new_name_input")
            if new_name and st.button("Create Customer"):
                new_cust, err = get_api_response("/customers", "POST", {"name": new_name})
                if not err:
                    st.session_state.current_customer = new_cust
                    st.success(f"Created: {new_name}")
                    st.rerun()

    with col2:
        st.subheader("📋 Customer Info")
        if st.session_state.current_customer:
            c = st.session_state.current_customer
            st.markdown(f"**Name:** {c['name']}")
            st.markdown(f"**Status:** {c.get('lead_status', 'New')}")
            st.markdown(f"**Budget:** {c.get('budget') or 'Not set'}")
        else:
            st.info("Select or create a customer to begin")

    st.markdown("---")

    if st.session_state.current_customer:
        if st.button("📞 Start Call", use_container_width=True, type="primary"):
            st.session_state.call_active = True
            st.session_state.chat_messages = []
            st.session_state.conversation_history = []
            st.session_state.show_summary = False
            st.session_state.summary_data = None
            st.session_state.lead_result = None
            st.rerun()
    else:
        st.warning("Please select or create a customer to start the call")


elif st.session_state.show_summary:

    # Summary screen
    render_summary(
        st.session_state.summary_data,
        st.session_state.current_customer["name"] if st.session_state.current_customer else "Customer"
    )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Back to Call", use_container_width=True):
            st.session_state.show_summary = False
            st.session_state.call_active = True
            st.rerun()
    with col2:
        if st.button("🏠 End & New Call", use_container_width=True):
            st.session_state.show_summary = False
            st.session_state.call_active = False
            st.session_state.chat_messages = []
            st.session_state.conversation_history = []
            st.rerun()


else:
    # Active call screen
    name = st.session_state.current_customer["name"]
    duration = len(st.session_state.conversation_history)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"# 📞 {name}")
        st.caption(f"🟢 Call Active — {duration} exchanges")
    with col2:
        if st.button("📵 End Call", type="secondary"):
            st.session_state.call_active = False
            st.session_state.chat_messages = []
            st.session_state.conversation_history = []
            st.session_state.last_audio = None
            st.rerun()

    st.markdown("---")

    # Conversation bubbles
    st.markdown("### 💬 Conversation")
    with st.container(border=True, height=350):
        if st.session_state.chat_messages:
            for msg in st.session_state.chat_messages:
                if msg["type"] == "user":
                    st.markdown(f"<div class='user-bubble'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='agent-bubble'>🤖 {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.info("🎙️ Call started — speak your first message below")

    # Audio player
    if st.session_state.last_audio and len(st.session_state.last_audio) > 100:
        st.audio(st.session_state.last_audio, format="audio/mp3", autoplay=True)
        st.session_state.last_audio = None

    st.markdown("---")
    st.markdown("### 🎙️ Speak Now")
    audio_data = st.audio_input("Click mic to record:", key=f"voice_{len(st.session_state.chat_messages)}")

    if audio_data:
        with st.spinner("Processing..."):
            if process_voice_message(audio_data):
                st.rerun()

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎯 Qualify Lead", use_container_width=True):
            result, error = get_api_response("/qualify-lead", "POST", {
                "customer_id": st.session_state.current_customer["id"],
                "buying_timeline": "This week",
            })
            if not error:
                st.session_state.lead_result = result
                st.rerun()

    with col2:
        if st.button("📅 Book Appointment", use_container_width=True):
            result, error = get_api_response("/appointments", "POST", {
                "customer_id": st.session_state.current_customer["id"],
                "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "reason": "Product Demo",
            })
            if not error:
                st.session_state.appointment_result = result
                st.rerun()

    with col3:
        if st.button("📋 View Summary", use_container_width=True, type="primary"):
            if st.session_state.conversation_history:
                result, error = get_api_response("/call-summary", "POST", {
                    "customer_id": st.session_state.current_customer["id"],
                    "conversation_history": st.session_state.conversation_history,
                })
                if not error:
                    st.session_state.summary_data = result["summary"]
                    st.session_state.show_summary = True
                    st.session_state.call_active = False
                    st.rerun()
                else:
                    st.error(f"Error: {error}")
            else:
                st.warning("Have a conversation first")

    # Show lead result
    if st.session_state.lead_result:
        r = st.session_state.lead_result
        status = r["lead_status"]
        badge_class = f"{status.lower()}-badge"
        st.markdown(f"""
        <div class='summary-card'>
            <strong>🎯 Lead Qualification Result</strong><br><br>
            Status: <span class='{badge_class}'>{status}</span><br><br>
            <small>{r.get('reasoning', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    # Show appointment result
    if st.session_state.appointment_result:
        r = st.session_state.appointment_result
        st.markdown(f"""
        <div class='summary-card'>
            <strong>📅 Appointment Booked!</strong><br><br>
            Date: {r.get('appointment_date', 'Tomorrow')[:10]}<br>
            Reason: {r.get('reason', 'Product Demo')}<br>
            Status: ✅ {r.get('status', 'Scheduled')}
        </div>
        """, unsafe_allow_html=True)
