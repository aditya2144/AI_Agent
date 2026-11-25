"""Streamlit frontend for the AI Sales Voice Agent."""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Tuple

# Configure page
st.set_page_config(
    page_title="TechStore AI Sales Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# API base URL
API_URL = "http://localhost:8000/api"

# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "current_customer" not in st.session_state:
    st.session_state.current_customer = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


def get_api_response(endpoint: str, method: str = "GET", data: dict = None):
    """Make API request."""
    try:
        url = f"{API_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            return response.json(), None
        else:
            return None, response.text
    except Exception as e:
        return None, str(e)


# ==================== Main Dashboard ====================

def main():
    """Main application."""
    
    # Sidebar navigation
    st.sidebar.markdown("# 🤖 TechStore AI Sales Agent")
    page = st.sidebar.radio(
        "Navigation",
        ["📊 Dashboard", "💬 AI Sales Assistant", "👥 Lead Management", 
         "📅 Appointments", "📝 Call Summaries", "📈 Analytics"]
    )
    
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "💬 AI Sales Assistant":
        show_chat()
    elif page == "👥 Lead Management":
        show_lead_management()
    elif page == "📅 Appointments":
        show_appointments()
    elif page == "📝 Call Summaries":
        show_call_summaries()
    elif page == "📈 Analytics":
        show_analytics()


def show_dashboard():
    """Show dashboard page."""
    st.title("📊 Dashboard")
    
    # Get statistics
    stats, error = get_api_response("/dashboard/stats")
    
    if error:
        st.error(f"Error loading statistics: {error}")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Customers", stats["total_customers"], delta=None)
    
    with col2:
        st.metric("Hot Leads", stats["hot_leads"], delta=None)
    
    with col3:
        st.metric("Scheduled Appointments", stats["scheduled_appointments"], delta=None)
    
    with col4:
        st.metric("Avg. Sentiment", stats["average_sentiment"], delta=None)
    
    # Lead distribution
    st.subheader("Lead Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        lead_data = {
            "Status": ["Hot", "Warm", "Cold"],
            "Count": [stats["hot_leads"], stats["warm_leads"], stats["cold_leads"]]
        }
        df_leads = pd.DataFrame(lead_data)
        st.bar_chart(df_leads.set_index("Status"))
    
    with col2:
        appointment_data = {
            "Status": ["Scheduled", "Completed"],
            "Count": [stats["scheduled_appointments"], stats["completed_appointments"]]
        }
        df_appointments = pd.DataFrame(appointment_data)
        st.bar_chart(df_appointments.set_index("Status"))
    
    # Recent customers
    st.subheader("Recent Customers")
    customers, error = get_api_response("/customers")
    
    if not error and customers:
        df_customers = pd.DataFrame([
            {
                "Name": c["name"],
                "Budget": f"${c['budget']:.2f}" if c["budget"] else "N/A",
                "Status": c["lead_status"],
                "Sentiment": c["sentiment"] or "N/A",
                "Created": datetime.fromisoformat(c["created_at"]).strftime("%Y-%m-%d %H:%M")
            }
            for c in customers[-10:]
        ])
        st.dataframe(df_customers, use_container_width=True)


def show_chat():
    """Show chat interface."""
    st.title("💬 AI Sales Assistant")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Voice & Text Chat")
    
    with col2:
        if st.button("New Chat"):
            st.session_state.chat_messages = []
            st.session_state.current_customer = None
            st.rerun()
    
    # Customer selection or creation
    st.markdown("### 👤 Customer Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get existing customers
        customers, _ = get_api_response("/customers")
        customer_names = ["New Customer"] + [c["name"] for c in (customers or [])]
        selected_customer = st.selectbox("Select Customer", customer_names)
        
        if selected_customer != "New Customer":
            st.session_state.current_customer = next(
                (c for c in customers if c["name"] == selected_customer),
                None
            )
        else:
            st.session_state.current_customer = None
    
    with col2:
        if selected_customer == "New Customer":
            customer_name = st.text_input("Customer Name", placeholder="Enter customer name")
            if customer_name:
                # Create new customer
                new_customer, error = get_api_response(
                    "/customers",
                    "POST",
                    {"name": customer_name}
                )
                if not error:
                    st.session_state.current_customer = new_customer
                    st.success(f"Customer '{customer_name}' created!")
    
    # Chat display
    st.markdown("### 💬 Conversation")
    
    # Display chat history
    for message in st.session_state.chat_messages:
        if message["type"] == "user":
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**Agent:** {message['content']}")
    
    # Chat input
    st.markdown("### 📝 Send Message")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("Type your message...", key="chat_input")
    
    with col2:
        send_button = st.button("Send", key="send_button")
    
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_messages.append({
            "type": "user",
            "content": user_input
        })
        
        # Get AI response
        chat_request = {
            "customer_id": st.session_state.current_customer["id"] if st.session_state.current_customer else None,
            "customer_name": st.session_state.current_customer["name"] if st.session_state.current_customer else "Unknown",
            "message": user_input,
            "conversation_history": st.session_state.conversation_history
        }
        
        response, error = get_api_response("/chat", "POST", chat_request)
        
        if error:
            st.error(f"Error: {error}")
        else:
            # Add agent response
            st.session_state.chat_messages.append({
                "type": "assistant",
                "content": response["response"]
            })
            
            # Update conversation history
            st.session_state.conversation_history.append([
                user_input,
                response["response"]
            ])
            
            st.rerun()
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Qualify Lead"):
            if st.session_state.current_customer:
                qualify_data = {
                    "customer_id": st.session_state.current_customer["id"],
                    "buying_timeline": "This week",
                }
                result, error = get_api_response("/qualify-lead", "POST", qualify_data)
                if not error:
                    st.success(f"Lead Status: {result['lead_status']}")
                    st.info(f"Reasoning: {result['reasoning']}")
                else:
                    st.error(f"Error: {error}")
    
    with col2:
        if st.button("Book Appointment"):
            if st.session_state.current_customer:
                appointment_date = datetime.now() + timedelta(days=1)
                appointment_data = {
                    "customer_id": st.session_state.current_customer["id"],
                    "appointment_date": appointment_date.isoformat(),
                    "reason": "Product Consultation",
                }
                result, error = get_api_response("/appointments", "POST", appointment_data)
                if not error:
                    st.success(f"Appointment booked for {result['appointment_date']}")
                else:
                    st.error(f"Error: {error}")
    
    with col3:
        if st.button("Generate Summary"):
            if st.session_state.chat_messages:
                summary_data = {
                    "customer_id": st.session_state.current_customer["id"] if st.session_state.current_customer else 1,
                    "conversation_history": st.session_state.conversation_history,
                }
                result, error = get_api_response("/call-summary", "POST", summary_data)
                if not error:
                    st.markdown("### 📄 Call Summary")
                    st.text_area("Summary", value=result["summary"], height=200, disabled=True)
                else:
                    st.error(f"Error: {error}")


def show_lead_management():
    """Show lead management page."""
    st.title("👥 Lead Management")
    
    # Get all customers
    customers, error = get_api_response("/customers")
    
    if error:
        st.error(f"Error loading customers: {error}")
        return
    
    if not customers:
        st.info("No customers found")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["Hot", "Warm", "Cold", "New", "Qualified"],
            default=["Hot", "Warm", "Cold", "New"]
        )
    
    with col2:
        sentiment_filter = st.multiselect(
            "Filter by Sentiment",
            ["Positive", "Neutral", "Negative"],
            default=["Positive", "Neutral", "Negative"]
        )
    
    with col3:
        budget_min = st.number_input("Min Budget", value=0, step=100)
    
    # Filter customers
    filtered_customers = [
        c for c in customers
        if c["lead_status"] in status_filter
        and (c["sentiment"] in sentiment_filter or c["sentiment"] is None)
        and (c["budget"] is None or c["budget"] >= budget_min)
    ]
    
    # Display customers table
    st.subheader(f"Customers ({len(filtered_customers)} found)")
    
    if filtered_customers:
        df = pd.DataFrame([
            {
                "ID": c["id"],
                "Name": c["name"],
                "Email": c["email"] or "N/A",
                "Phone": c["phone"] or "N/A",
                "Budget": f"${c['budget']:.2f}" if c["budget"] else "N/A",
                "Status": c["lead_status"],
                "Sentiment": c["sentiment"] or "N/A",
                "Timeline": c["buying_timeline"] or "N/A"
            }
            for c in filtered_customers
        ])
        
        st.dataframe(df, use_container_width=True)
        
        # Detail view
        selected_id = st.selectbox("Select customer to view details", [c["id"] for c in filtered_customers])
        
        if selected_id:
            customer = next((c for c in filtered_customers if c["id"] == selected_id), None)
            if customer:
                st.markdown(f"### {customer['name']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Email:** {customer['email'] or 'N/A'}")
                    st.write(f"**Phone:** {customer['phone'] or 'N/A'}")
                    st.write(f"**Budget:** ${customer['budget']:.2f}" if customer['budget'] else "**Budget:** N/A")
                
                with col2:
                    st.write(f"**Status:** {customer['lead_status']}")
                    st.write(f"**Sentiment:** {customer['sentiment'] or 'N/A'}")
                    st.write(f"**Timeline:** {customer['buying_timeline'] or 'N/A'}")
                
                if customer['requirements']:
                    st.write(f"**Requirements:** {customer['requirements']}")


def show_appointments():
    """Show appointments page."""
    st.title("📅 Appointments")
    
    # Get all appointments
    appointments, error = get_api_response("/appointments")
    
    if error:
        st.error(f"Error loading appointments: {error}")
        return
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["Upcoming", "All Appointments"])
    
    with tab1:
        st.subheader("Upcoming Appointments")
        
        if appointments:
            # Filter upcoming appointments
            upcoming = [
                a for a in appointments
                if datetime.fromisoformat(a["appointment_date"]) > datetime.now()
            ]
            
            if upcoming:
                df = pd.DataFrame([
                    {
                        "ID": a["id"],
                        "Customer ID": a["customer_id"],
                        "Date": datetime.fromisoformat(a["appointment_date"]).strftime("%Y-%m-%d %H:%M"),
                        "Reason": a["reason"] or "N/A",
                        "Status": a["status"],
                    }
                    for a in upcoming
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No upcoming appointments")
    
    with tab2:
        st.subheader("All Appointments")
        
        if appointments:
            df = pd.DataFrame([
                {
                    "ID": a["id"],
                    "Customer ID": a["customer_id"],
                    "Date": datetime.fromisoformat(a["appointment_date"]).strftime("%Y-%m-%d %H:%M"),
                    "Reason": a["reason"] or "N/A",
                    "Status": a["status"],
                }
                for a in appointments
            ])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No appointments found")


def show_call_summaries():
    """Show call summaries page."""
    st.title("📝 Call Summaries")
    
    # Get all customers
    customers, _ = get_api_response("/customers")
    
    if not customers:
        st.info("No customers found")
        return
    
    # Select customer
    selected_customer = st.selectbox(
        "Select Customer",
        customers,
        format_func=lambda c: c["name"]
    )
    
    if selected_customer:
        # Get call summaries for customer
        summaries, error = get_api_response(f"/call-summaries/{selected_customer['id']}")
        
        if error:
            st.error(f"Error loading summaries: {error}")
            return
        
        if summaries:
            st.subheader(f"Call Summaries for {selected_customer['name']}")
            
            for summary in summaries:
                with st.expander(f"Summary from {datetime.fromisoformat(summary['created_at']).strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(summary["summary"])
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Sentiment:** {summary['sentiment'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Budget:** ${summary['budget']:.2f}" if summary['budget'] else "**Budget:** N/A")
                    
                    with col3:
                        st.write(f"**Lead Class:** {summary['lead_classification'] or 'N/A'}")
        else:
            st.info(f"No call summaries for {selected_customer['name']}")


def show_analytics():
    """Show analytics page."""
    st.title("📈 Analytics")
    
    # Get statistics
    stats, _ = get_api_response("/dashboard/stats")
    
    if stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Conversations", stats["conversation_count"])
        
        with col2:
            conversion_rate = 0
            if stats["total_customers"] > 0:
                conversion_rate = (stats["hot_leads"] / stats["total_customers"]) * 100
            st.metric("Hot Lead Conversion %", f"{conversion_rate:.1f}%")
        
        with col3:
            if stats["scheduled_appointments"] + stats["completed_appointments"] > 0:
                completion_rate = (stats["completed_appointments"] / 
                                 (stats["scheduled_appointments"] + stats["completed_appointments"])) * 100
            else:
                completion_rate = 0
            st.metric("Appointment Completion %", f"{completion_rate:.1f}%")
        
        # Lead progression
        st.subheader("Lead Status Progression")
        
        lead_data = {
            "New": stats["total_customers"] - stats["hot_leads"] - stats["warm_leads"] - stats["cold_leads"],
            "Cold": stats["cold_leads"],
            "Warm": stats["warm_leads"],
            "Hot": stats["hot_leads"],
        }
        
        df_leads = pd.DataFrame([lead_data])
        st.bar_chart(df_leads.T)


if __name__ == "__main__":
    main()
