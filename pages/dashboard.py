import streamlit as st

# Check Login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Please login first.")
    st.stop()

st.set_page_config(page_title="Dashboard", layout="wide")

st.markdown("""
<style>

.stButton button {
    height: 3em;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

st.markdown(
f"""
<div style="background-color:#667eea; padding:25px; border-radius:15px;">

<h1 style="color:white;">🎯 AI Interview Coach</h1>
<h3 style="color:white;">Welcome, {st.session_state.user} 👋</h3>
<p style="color:white;">Practice interviews, improve confidence and get AI-powered feedback.</p>

</div>
""",
unsafe_allow_html=True
)


st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.info("📄 Resume Analysis\n\nUpload your resume and get AI-based analysis.")

    if st.button("Upload Resume", use_container_width=True):
        st.switch_page("pages/resume_upload.py")


with col2:
    st.success("🎤 Mock Interview\n\nPractice real interview questions with AI.")

    if st.button("Start Interview", use_container_width=True):
        st.switch_page("pages/interview.py")
st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.warning("📜 Interview History\n\nView your previous interview performance.")

    if st.button("View History", use_container_width=True):
        st.switch_page("pages/history.py")


with col4:
    st.error("🚪 Logout\n\nExit from your account safely.")

    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/login.py")