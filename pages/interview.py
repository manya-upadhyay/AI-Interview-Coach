import streamlit as st
import re
import json
import os
import time
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
from utils.confidence_analyzer import (
    analyze_frame,
    get_confidence_result
)
from utils.speech_to_text import recognize_speech, recognize_speech_from_audio
from utils.ai_helper import (
    generate_interview_questions,
    evaluate_answer,
    evaluate_interview
)
from utils.pdf_generator import generate_pdf
from database.database import save_interview

# Ensure required directories exist
os.makedirs("reports", exist_ok=True)
os.makedirs("database", exist_ok=True)

class VideoProcessor(VideoProcessorBase):

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        processed_frame, score, eye_status, smile_status = analyze_frame(img)
        return av.VideoFrame.from_ndarray(
            processed_frame,
            format="bgr24"
        )

# ---------------- LOGIN CHECK ---------------- #
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Please login first.")
    st.switch_page("pages/login.py")

st.markdown(
"""
<div style="
background:linear-gradient(135deg,#111827,#1D4ED8);
padding:25px;
border-radius:15px;
">

<h1 style="color:white;">
🎤 AI Mock Interview
</h1>

<p style="color:white;font-size:17px;">
Practice real interview scenarios with AI feedback,
voice analysis and confidence tracking.
</p>

</div>
""",
unsafe_allow_html=True
)

resume_text = st.session_state.get("resume_text", "")

# ---------------- SESSION VARIABLES ---------------- #
if "questions" not in st.session_state:
    st.session_state.questions = []

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = time.time()

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False

# ---------------- SHOW COMPLETED REPORT ---------------- #
if st.session_state.get("interview_completed", False):
    report = st.session_state.get("interview_report", {})

    st.success("Interview Completed 🎉")
    st.subheader("📊 AI Interview Report")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("⭐ Overall Score", f"{report.get('overall_score', 0)}/100")
        st.metric("💻 Technical", f"{report.get('technical', 0)}/10")
        st.metric("🧠 Problem Solving", f"{report.get('problem_solving', 0)}/10")

    with col2:
        st.metric("🗣 Communication", f"{report.get('communication', 0)}/10")
        st.metric("😊 Confidence", f"{report.get('confidence_score', 0)}%")

    st.markdown("---")

    st.subheader("✅ Strengths")
    for item in report.get("strengths", []):
        st.success(item)

    st.subheader("⚠ Weaknesses")
    for item in report.get("weaknesses", []):
        st.warning(item)

    st.subheader("💡 Suggestions")
    for item in report.get("suggestions", []):
        st.info(item)

    st.subheader("🎯 Final Recommendation")
    st.success(report.get("final_recommendation", "N/A"))

    st.markdown("---")

    pdf_bytes = st.session_state.get("pdf_bytes")
    if not pdf_bytes:
        pdf_path = st.session_state.get("pdf_path", "reports/interview_report.pdf")
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf:
                pdf_bytes = pdf.read()
                st.session_state.pdf_bytes = pdf_bytes
        elif report:
            try:
                pdf_path = generate_pdf(json.dumps(report, indent=4))
                with open(pdf_path, "rb") as pdf:
                    pdf_bytes = pdf.read()
                    st.session_state.pdf_bytes = pdf_bytes
            except Exception as e:
                print("PDF generation error:", e)

    if pdf_bytes:
        st.download_button(
            "📄 Download Report PDF",
            data=pdf_bytes,
            file_name="Interview_Report.pdf",
            mime="application/pdf",
            key="download_pdf_report"
        )


    st.markdown("---")
    if st.button("🔄 Start New Interview"):
        st.session_state.interview_completed = False
        st.session_state.interview_report = None
        st.session_state.questions = []
        st.session_state.current_question = 0
        st.session_state.answers = {}
        if "report_saved" in st.session_state:
            del st.session_state.report_saved
        st.rerun()

    st.stop()

# ---------------- INTERVIEW SETUP ---------------- #
st.subheader("🎯 Select Interview Type")

interview_type = st.selectbox(
    "Choose Interview Type",
    [
        "Technical Interview",
        "HR Interview",
        "Behavioral Interview",
        "Resume Based Interview",
        "Mixed Interview"
    ]
)

st.session_state.interview_type = interview_type

if not resume_text:
    st.warning("Please upload your resume first.")
    st.stop()

# ---------------- GENERATE QUESTIONS ---------------- #
if st.button("🤖 Generate Interview Questions"):
    with st.spinner("🤖 AI is analyzing your resume and preparing questions..."):
        try:
            questions = generate_interview_questions(
                st.session_state.interview_type,
                resume_text
            )
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ Gemini API quota exceeded. Please try again later or use another API key.")
            else:
                st.error(f"⚠️ {e}")
            st.stop()

        st.session_state.questions = questions
        st.session_state.current_question = 0
        st.session_state.question_start_time = time.time()
        st.session_state.answers = {}
        st.rerun()

# ---------------- SHOW QUESTIONS ---------------- #
if st.session_state.questions:

    index = st.session_state.current_question

    st.subheader(
        f"Question {index+1} / {len(st.session_state.questions)}"
    )

    progress = (index + 1) / len(st.session_state.questions)
    st.progress(progress)

    st.info(st.session_state.questions[index])

    st.subheader("📷 Confidence Analysis")

    camera_on = st.toggle("Start Camera")

    if camera_on:
        webrtc_streamer(
            key="confidence-camera",
            video_processor_factory=VideoProcessor,
            media_stream_constraints={
                "video": True,
                "audio": False,
            },
        )

    TIME_LIMIT = 120  # 2 minutes

    elapsed = int(time.time() - st.session_state.question_start_time)
    remaining = max(0, TIME_LIMIT - elapsed)

    minutes = remaining // 60
    seconds = remaining % 60

    st.metric("⏳ Time Left", f"{minutes:02d}:{seconds:02d}")

    if remaining == 0:
        st.warning("⏰ Time's Up!")
        if index < len(st.session_state.questions) - 1:
            st.session_state.current_question += 1
            st.session_state.question_start_time = time.time()
            st.rerun()

    if f"answer_{index}" not in st.session_state:
        st.session_state[f"answer_{index}"] = ""

    # ---------------- VOICE RECORDING (BROWSER MIC & SYSTEM MIC) ---------------- #
    st.write("#### 🎤 Answer via Voice Recording")
    
    # Browser Audio Input (Works on Streamlit Cloud & Browsers!)
    audio_val = st.audio_input("Record your answer (Browser Mic)", key=f"audio_input_{index}")

    if audio_val is not None:
        audio_key = f"transcribed_audio_{index}"
        audio_id = str(len(audio_val.getvalue()))
        if st.session_state.get(audio_key) != audio_id:
            with st.spinner("🎤 Processing browser recording... Converting voice into text..."):
                speech_text = recognize_speech_from_audio(audio_val)
                st.session_state[audio_key] = audio_id
                if speech_text:
                    st.session_state[f"answer_{index}"] = speech_text
                    st.success("✅ Voice converted to text!")
                    st.rerun()
                else:
                    st.warning("⚠️ Could not recognize speech. Please speak clearly into your mic.")

    col_rec1, col_rec2 = st.columns(2)
    with col_rec1:
        if st.button("🎤 Record via System Mic (Local)", key=f"record_local_{index}"):
            with st.spinner("🎤 Listening via local microphone... Speak now!"):
                speech_text = recognize_speech()
                if speech_text:
                    st.session_state[f"answer_{index}"] = speech_text
                    st.success("✅ Voice converted to text")
                    st.rerun()
                else:
                    st.warning("⚠️ No speech detected or local microphone unavailable.")

    answer = st.text_area(
        "Your Answer (Edit or Type here)",
        key=f"answer_{index}"
    )

    # ---------------- AI FEEDBACK ---------------- #
    if st.button("🧠 Evaluate This Answer"):
        if answer.strip() == "":
            st.warning("Please enter or record your answer first.")
        else:
            with st.spinner("🧠 AI is evaluating your answer and generating feedback..."):
                try:
                    feedback = evaluate_answer(
                        st.session_state.questions[index],
                        answer
                    )
                except Exception:
                    st.error("⚠️ Unable to evaluate your answer right now. Please try again.")
                    st.stop()

            st.subheader("📝 AI Feedback")
            st.markdown(feedback)

    st.session_state.answers[index] = answer

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Previous"):
            if index > 0:
                st.session_state.current_question -= 1
                st.session_state.question_start_time = time.time()
                st.rerun()

    with col2:
        if index < len(st.session_state.questions) - 1:
            if st.button("Next ➡"):
                st.session_state.current_question += 1
                st.session_state.question_start_time = time.time()
                st.rerun()

        else:
            if st.button("✅ Finish Interview"):
                report = None
                with st.spinner("📊 AI is analyzing your complete interview performance..."):
                    try:
                        report = evaluate_interview(
                            st.session_state.questions,
                            st.session_state.answers
                        )
                    except Exception as e:
                        st.error(f"⚠️ Unable to generate interview report: {e}")
                        st.stop()

                if report:
                    try:
                        confidence = get_confidence_result()
                        report["confidence_score"] = confidence["score"]
                        report["eye_status"] = confidence["eye_status"]
                        report["smile_status"] = confidence["smile_status"]
                    except Exception:
                        report["confidence_score"] = 75
                        report["eye_status"] = "Good"
                        report["smile_status"] = "Yes"

                    score = report.get("overall_score", 0)

                    # Save report to database safely
                    if "report_saved" not in st.session_state:
                        try:
                            user_email = st.session_state.get("email") or st.session_state.get("user") or "candidate@example.com"
                            save_interview(
                                user_email,
                                score,
                                json.dumps(report, indent=4)
                            )
                            st.session_state.report_saved = True
                        except Exception as db_err:
                            print("DB save warning:", db_err)

                    # Generate PDF report safely
                    try:
                        pdf_path = generate_pdf(json.dumps(report, indent=4))
                        st.session_state.pdf_path = pdf_path
                    except Exception as pdf_err:
                        print("PDF generation warning:", pdf_err)

                    # Store state and rerun to show report
                    st.session_state.interview_report = report
                    st.session_state.interview_completed = True
                    st.rerun()
