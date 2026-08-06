import streamlit as st
import os
from utils.ai_helper import analyze_resume
from utils.resume_parser import extract_text

# ---------------- LOGIN CHECK ---------------- #

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Please login first.")
    st.switch_page("pages/login.py")

st.set_page_config(page_title="Resume Upload", layout="wide")

st.title("📄 Resume Upload")

uploaded_file = st.file_uploader(
    "Upload your Resume",
    type=["pdf", "docx"]
)

if uploaded_file:

    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join("uploads", uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("✅ Resume Uploaded Successfully!")

    text = extract_text(file_path)

    st.session_state.resume_text = text

    st.subheader("📄 Resume Preview")

    st.text_area(
        "Resume Text",
        text,
        height=250
    )

    if st.button("🤖 Analyze Resume"):

        with st.spinner("Analyzing Resume..."):

            result = analyze_resume(text)

        # Save result for future pages
        st.session_state.resume_analysis = result

        st.success("Analysis Completed ✅")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "📄 Resume Score",
                f"{result['resume_score']}/100"
            )

        with col2:
            st.metric(
                "🎯 ATS Score",
                f"{result['ats_score']}/100"
            )

        st.markdown("---")

        st.subheader("👤 Candidate Details")

        st.write("**Name:**", result["candidate_name"])
        st.write("**Email:**", result["email"])

        st.write("**Recommended Career:**")
        st.success(result["career_recommendation"])

        st.markdown("---")

        st.subheader("💻 Skills")

        if result["skills"]:
            for skill in result["skills"]:
                st.success(skill)

        st.subheader("❌ Missing Skills")

        if result["missing_skills"]:
            for skill in result["missing_skills"]:
                st.warning(skill)

        st.markdown("---")

        st.subheader("🎓 Education")

        for edu in result["education"]:
            st.write("•", edu)

        st.markdown("---")

        st.subheader("🚀 Projects")

        for project in result["projects"]:
            st.write("•", project)

        st.markdown("---")

        st.subheader("💪 Strengths")

        for s in result["strengths"]:
            st.success(s)

        st.subheader("⚠ Weaknesses")

        for w in result["weaknesses"]:
            st.warning(w)

        st.markdown("---")

        st.subheader("💡 Suggestions")

        for s in result["suggestions"]:
            st.info(s)

        st.balloons()