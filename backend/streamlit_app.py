"""
Streamlit Demo UI for the Collections Intelligence Agent.

Run with:
    cd backend
    .\venv\Scripts\Activate.ps1
    streamlit run streamlit_app.py
"""
import streamlit as st
import requests
import json

# --- Configuration ---
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Collections Intelligence Agent",
    page_icon="🏦",
    layout="wide",
)


# --- Helper Functions ---
def call_api(endpoint: str, method: str = "GET", payload: dict = None):
    """Make API call to FastAPI backend."""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            resp = requests.get(url, timeout=30)
        else:
            resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend not running! Start with: `uvicorn app.main:app --reload`")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API Error: {e.response.status_code} — {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None


def get_customers():
    """Fetch all customers from API."""
    data = call_api("/customers/")
    return data if data else []


def get_loans(customer_id: str):
    """Fetch loans for a customer."""
    data = call_api(f"/loans/customer/{customer_id}")
    return data if data else []


def get_payments(loan_id: str):
    """Fetch payments for a loan."""
    data = call_api(f"/payments/loan/{loan_id}")
    return data if data else []


def get_risk_assessment(customer_id: str, loan_id: str):
    """Fetch full risk assessment."""
    data = call_api(f"/analytics/risk-assessment/{customer_id}?loan_id={loan_id}", method="POST")
    return data


def run_workflow(customer_id: str, message: str):
    """Run the LangGraph workflow pipeline."""
    payload = {"customer_id": customer_id, "message": message}
    return call_api("/workflow/process", method="POST", payload=payload)


# --- Sidebar: Customer Selection ---
st.sidebar.image("Union_Bank_of_India_Logo.svg.png", width=200)
st.sidebar.title("Collections Agent")
st.sidebar.markdown("---")

customers = get_customers()
if not customers:
    st.sidebar.warning("No customers found. Run seed_data.py first.")
    st.stop()

customer_options = {f"{c['customer_id']} — {c['customer_name']}": c for c in customers}
selected_label = st.sidebar.selectbox("Select Customer", list(customer_options.keys()))
selected_customer = customer_options[selected_label]
customer_id = selected_customer["customer_id"]

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Customer Info")
st.sidebar.markdown(f"**Name:** {selected_customer['customer_name']}")
st.sidebar.markdown(f"**Employment:** {selected_customer['employment_type']}")
st.sidebar.markdown(f"**Income:** ₹{selected_customer['monthly_income']:,.0f}")
st.sidebar.markdown(f"**Credit Score:** {selected_customer['credit_score']}")
st.sidebar.markdown(f"**Language:** {selected_customer.get('preferred_language', 'English')}")

# --- Fetch Loan Data ---
loans = get_loans(customer_id)
if loans:
    loan = loans[0]
    loan_id = loan["loan_id"]
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 Loan Info")
    st.sidebar.markdown(f"**Loan ID:** {loan_id}")
    st.sidebar.markdown(f"**Type:** {loan['loan_type']}")
    st.sidebar.markdown(f"**Amount:** ₹{loan['loan_amount']:,.0f}")
    st.sidebar.markdown(f"**Outstanding:** ₹{loan['outstanding_balance']:,.0f}")
    st.sidebar.markdown(f"**EMI:** ₹{loan['emi_amount']:,.0f}")
    st.sidebar.markdown(f"**Days Past Due:** {loan['days_past_due']}")
else:
    loan = None
    loan_id = None

# --- Main Area ---
st.title("🤖 Collections Intelligence Agent")
st.markdown("Pre-delinquency AI system — Analyze risk, get recovery strategies with explainable AI.")
st.markdown("---")

# --- Tabs ---
tab_chat, tab_risk, tab_analytics, tab_payments = st.tabs([
    "💬 Chat with Agent", "📊 Risk Dashboard", "📈 Analytics", "💰 Payment History"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1: Chat Interface
# ═══════════════════════════════════════════════════════════════
with tab_chat:
    st.subheader("💬 Chat with Collections Agent")
    st.markdown("Ask questions in **English or Hindi**. The agent will analyze the customer and respond.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about this customer's risk, strategy, etc..."):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call workflow
        with st.chat_message("assistant"):
            with st.spinner("🔄 Running analysis pipeline..."):
                result = run_workflow(customer_id, prompt)

            if result:
                response = result.get("response", "No response")
                lang = result.get("detected_language", "English")
                st.markdown(response)
                st.caption(f"🌐 Detected language: {lang}")
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.error("Failed to get response from agent.")

    # Quick action buttons
    st.markdown("---")
    st.markdown("**Quick Actions:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Full Risk Analysis", use_container_width=True):
            with st.spinner("Analyzing..."):
                result = run_workflow(customer_id, "Provide a complete risk analysis and recovery recommendation")
            if result:
                st.session_state.messages.append({"role": "user", "content": "Full Risk Analysis"})
                st.session_state.messages.append({"role": "assistant", "content": result.get("response", "")})
                st.rerun()

    with col2:
        if st.button("📋 Strategy Recommendation", use_container_width=True):
            with st.spinner("Analyzing..."):
                result = run_workflow(customer_id, "What is the best recovery strategy for this customer?")
            if result:
                st.session_state.messages.append({"role": "user", "content": "Strategy Recommendation"})
                st.session_state.messages.append({"role": "assistant", "content": result.get("response", "")})
                st.rerun()

    with col3:
        if st.button("🗣️ Hindi Analysis (हिंदी)", use_container_width=True):
            with st.spinner("Analyzing..."):
                result = run_workflow(customer_id, "इस ग्राहक का जोखिम विश्लेषण करें और वसूली रणनीति सुझाएं")
            if result:
                st.session_state.messages.append({"role": "user", "content": "हिंदी में विश्लेषण"})
                st.session_state.messages.append({"role": "assistant", "content": result.get("response", "")})
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# TAB 2: Risk Dashboard
# ═══════════════════════════════════════════════════════════════
with tab_risk:
    st.subheader("📊 Risk Dashboard")

    if loan:
        assessment = get_risk_assessment(customer_id, loan_id)

        if assessment:
            risk_profile = assessment.get("risk_profile", {})
            recommendation = assessment.get("recommendation", {})

            # Top metrics row
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                segment = risk_profile.get("customer_segment", "N/A")
                color = "🟢" if segment == "Self-Cure" else ("🟡" if segment == "Medium Risk" else "🔴")
                st.metric("Customer Segment", f"{color} {segment}")
            with m2:
                scp = risk_profile.get("self_cure_probability", 0)
                st.metric("Self-Cure Probability", f"{scp:.0%}")
            with m3:
                var = risk_profile.get("value_at_risk", 0)
                st.metric("Value at Risk", f"₹{var:,.0f}")
            with m4:
                dpd = loan["days_past_due"]
                st.metric("Days Past Due", dpd)

            st.markdown("---")

            # Recommendation card
            st.markdown("### 🎯 Recommended Strategy")
            rec_col1, rec_col2 = st.columns(2)
            with rec_col1:
                st.info(f"**Action:** {recommendation.get('recommended_action', 'N/A')}")
                st.info(f"**Risk Level:** {recommendation.get('risk_level', 'N/A')}")
            with rec_col2:
                exp_rec = recommendation.get("expected_recovery", 0)
                est_npv = recommendation.get("estimated_npv", 0)
                st.info(f"**Expected Recovery:** ₹{exp_rec:,.0f}")
                st.info(f"**Estimated NPV:** ₹{est_npv:,.0f}")

            # Reasoning factors
            factors = recommendation.get("reasoning_factors", [])
            if factors:
                st.markdown("### 📝 Reasoning Factors")
                for f in factors:
                    st.markdown(f"- {f}")

            # Risk factors breakdown
            risk_factors = risk_profile.get("risk_factors", {})
            if risk_factors:
                st.markdown("### 🔬 Risk Factor Breakdown")
                rf_col1, rf_col2, rf_col3 = st.columns(3)
                with rf_col1:
                    st.metric("Credit Score", risk_factors.get("credit_score", "N/A"))
                    st.metric("Payment Consistency", f"{risk_factors.get('payment_consistency', 0):.0%}")
                with rf_col2:
                    st.metric("Income/EMI Ratio", f"{risk_factors.get('income_to_emi_ratio', 0):.1f}x")
                    st.metric("Employment", risk_factors.get("employment_type", "N/A"))
                with rf_col3:
                    st.metric("DPD", risk_factors.get("days_past_due", 0))
                    st.metric("Delay Trend", risk_factors.get("delay_trend", "N/A"))
        else:
            st.warning("Could not load risk assessment.")
    else:
        st.warning("No loans found for this customer.")


# ═══════════════════════════════════════════════════════════════
# TAB 3: Analytics Detail
# ═══════════════════════════════════════════════════════════════
with tab_analytics:
    st.subheader("📈 Detailed Analytics")

    if loan:
        assessment = get_risk_assessment(customer_id, loan_id)

        if assessment:
            # Payment Trends
            trends = assessment.get("payment_trends", {})
            st.markdown("### 💳 Payment Trends")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            with t_col1:
                st.metric("Total Payments", trends.get("total_payments", 0))
            with t_col2:
                st.metric("On-Time", trends.get("on_time_payments", 0))
            with t_col3:
                st.metric("Late", trends.get("late_payments", 0))
            with t_col4:
                st.metric("Avg Delay (days)", trends.get("average_delay_days", 0))

            st.markdown("---")

            # Financial Exposure
            exposure = assessment.get("financial_exposure", {})
            st.markdown("### 💰 Financial Exposure")
            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                st.metric("Outstanding Balance", f"₹{exposure.get('outstanding_balance', 0):,.0f}")
            with e_col2:
                st.metric("Overdue Amount", f"₹{exposure.get('overdue_amount', 0):,.0f}")
            with e_col3:
                st.metric("Exposure Ratio", f"{exposure.get('exposure_ratio', 0):.2%}")

            st.markdown("---")

            # Delay Pattern
            delay = assessment.get("delay_pattern", {})
            st.markdown("### 📉 EMI Delay Pattern")
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                st.metric("Delay Trend", delay.get("delay_trend", "N/A"))
            with d_col2:
                st.metric("Recent Delay (days)", delay.get("recent_delay_days", 0))
            with d_col3:
                worsening = "⚠️ Yes" if delay.get("is_worsening") else "✅ No"
                st.metric("Worsening?", worsening)
        else:
            st.warning("Could not load analytics.")
    else:
        st.warning("No loans found for this customer.")


# ═══════════════════════════════════════════════════════════════
# TAB 4: Payment History
# ═══════════════════════════════════════════════════════════════
with tab_payments:
    st.subheader("💰 Payment History")

    if loan_id:
        payments = get_payments(loan_id)
        if payments:
            # Display as table
            import pandas as pd
            df = pd.DataFrame(payments)
            display_cols = ["payment_id", "payment_date", "payment_amount", "payment_method"]
            available_cols = [c for c in display_cols if c in df.columns]
            if available_cols:
                df_display = df[available_cols].copy()
                if "payment_amount" in df_display.columns:
                    df_display["payment_amount"] = df_display["payment_amount"].apply(lambda x: f"₹{x:,.0f}")
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                # Summary
                st.markdown("---")
                total_paid = sum(p.get("payment_amount", 0) for p in payments)
                st.markdown(f"**Total Payments:** {len(payments)} | **Total Paid:** ₹{total_paid:,.0f}")
            else:
                st.json(payments)
        else:
            st.info("No payments found for this loan.")
    else:
        st.warning("No loan selected.")


# --- Footer ---
st.markdown("---")
st.caption("Collections Intelligence Agent v1.0 | Powered by LangGraph + Llama-3 + ChromaDB")