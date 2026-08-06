import streamlit as st
from database.database import create_table

# Create database
create_table()

# Page Configuration
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a, #334155);
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: white;
}

/* Sidebar buttons/pages */
[data-testid="stSidebarNav"] a {
    border-radius: 10px;
    margin: 5px 0;
    padding: 8px 12px;
}

/* Hover effect */
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(255,255,255,0.15);
}

/* Selected page */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(255,255,255,0.2);
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# Title
st.markdown(
"""
<div style="background-color:#0F172A;
padding:30px;
border-radius:15px;">

<h1 style="color:white;">
🎯 AI Interview Coach
</h1>

<p style="color:white;font-size:18px;">
Your AI-powered platform to practice interviews,
analyze your performance and build confidence.
</p>

</div>
""",
unsafe_allow_html=True
)

with st.sidebar:
    st.markdown(
        """
        <h2 style="color:white;">
        🎯 AI Interview Coach
        </h2>
        <p style="color:#CBD5E1;">
        AI-powered platform to practice interviews,
        analyze performance and improve confidence.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

with st.sidebar:



    st.markdown(
        """
        <h3 style="color:white;">
        👤 Profile
        </h3>
        """,
        unsafe_allow_html=True
    )

    if "user" in st.session_state:
        st.write(f"Welcome, {st.session_state.user} 👋")

    if "email" in st.session_state:
        st.write(st.session_state.email)



st.divider()

st.markdown(
    """
    <p style="
    color:#94A3B8;
    font-size:13px;
    text-align:center;
    ">
    🚀 AI Powered Interview Preparation
    </p>
    """,
    unsafe_allow_html=True
)


st.markdown("""
## Welcome!

This AI-powered platform helps candidates prepare for interviews.

### Features
- 📄 Resume Analysis
- 🤖 AI Generated Interview Questions
- 🎤 Voice-based Interview
- 😊 Facial Confidence Analysis
- 📊 Performance Report
- 📥 PDF Report Download
""")

st.success("Project setup completed successfully! ✅")