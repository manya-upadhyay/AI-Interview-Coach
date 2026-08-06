import streamlit as st
import re
import json
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
from utils.confidence_analyzer import (
    analyze_frame,
    get_confidence_result
)
from utils.speech_to_text import recognize_speech
from utils.ai_helper import (
    generate_interview_questions,
    evaluate_answer,
    evaluate_interview
)
from streamlit_autorefresh import st_autorefresh
import time
from utils.pdf_generator import generate_pdf
from database.database import save_interview

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

# ---------------- SESSION VARIABLES ---------------- #

if "questions" not in st.session_state:
    st.session_state.questions = []

if "current_question" not in st.session_state:
    st.session_state.current_question = 0


#-----------time-------------------#
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = time.time()

#----------------answers--------------------#
if "answers" not in st.session_state:
    st.session_state.answers = {}

# ---------------- GENERATE QUESTIONS ---------------- #

if st.button("🤖 Generate Interview Questions"):
    with st.spinner("🤖 AI is analyzing your resume and preparing questions..."):
        prompt = f"""
        You are an expert interviewer.

        Interview Type:
        {st.session_state.interview_type}

        Candidate Resume:

        {resume_text}

        Generate exactly 10 interview questions.

        Rules:

        - Questions must match the selected interview type.
        - One question per line.
        - No numbering.
        - No explanation.
        - No headings.
        - Keep questions relevant to the candidate's resume.
        """

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

# ---------------- SHOW QUESTIONS ---------------- #

if st.session_state.questions:
    #st_autorefresh(interval=1000, key="interview_timer")

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

    if st.button("🎤 Record Answer", key=f"record_{index}"):
        with st.spinner("🎤 Listening to your answer... Converting voice into text..."):
            speech_text = recognize_speech()
            print("Speech Text =", repr(speech_text))

            st.session_state[f"answer_{index}"] = speech_text

        st.success("✅ Voice converted to text")

    answer = st.text_area(
        "Your Answer",
        key=f"answer_{index}"
    )

    # ---------------- AI FEEDBACK ---------------- #

    if st.button("🧠 Evaluate This Answer"):

        if answer.strip() == "":
            st.warning("Please enter your answer first.")

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
                    st.success("Interview Completed 🎉")

                    with st.spinner("📊 AI is analyzing your complete interview performance..."):
                        try:
                            report = evaluate_interview(
                                st.session_state.questions,
                                st.session_state.answers
                            )

                        except Exception:
                            st.error("⚠️ Unable to generate interview report. Please try again.")
                            st.stop()

                        score = report["overall_score"]


                        confidence = get_confidence_result()

                        report["confidence_score"] = confidence["score"]
                        report["eye_status"] = confidence["eye_status"]
                        report["smile_status"] = confidence["smile_status"]

                    st.subheader("📊 AI Interview Report")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("⭐ Overall Score", f"{report['overall_score']}/100")
                        st.metric("💻 Technical", f"{report['technical']}/10")
                        st.metric("🧠 Problem Solving", f"{report['problem_solving']}/10")

                    with col2:
                        st.metric("🗣 Communication", f"{report['communication']}/10")
                        st.metric("😊 Confidence", f"{confidence['score']}%")

                    st.markdown("---")

                    st.subheader("✅ Strengths")

                    for item in report["strengths"]:
                        st.success(item)

                    st.subheader("⚠ Weaknesses")

                    for item in report["weaknesses"]:
                        st.warning(item)

                    st.subheader("💡 Suggestions")

                    for item in report["suggestions"]:
                        st.info(item)

                    st.subheader("🎯 Final Recommendation")

                    st.success(report["final_recommendation"])
                    # Save report only once
                    if "report_saved" not in st.session_state:
                        save_interview(
                            st.session_state.email,
                            score,
                            json.dumps(report, indent=4)
                        )


                        st.session_state.report_saved = True
                    with st.spinner("📄 Creating your professional interview report PDF..."):
                        pdf_path = generate_pdf(
                            json.dumps(report, indent=4)
                        )

                    with open(pdf_path, "rb") as pdf:
                        st.download_button(
                            "📄 Download Report",
                            pdf,
                            file_name="Interview_Report.pdf",
                            mime="application/pdf"
                        )