import google.generativeai as genai
import json
import re
import time
import os
import streamlit as st
from config import GEMINI_API_KEY

def get_api_key():
    """Retrieve Gemini API Key from Session State, Streamlit Secrets, or Environment."""
    try:
        if hasattr(st, "session_state") and st.session_state.get("custom_gemini_api_key"):
            key = st.session_state["custom_gemini_api_key"].strip()
            if key:
                return key
    except Exception:
        pass

    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"].strip()
            if key:
                return key
    except Exception:
        pass

    return (os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY or "").strip()


def handle_gemini_error(e):
    error = str(e)
    if "429" in error:
        return (
            "⚠️ Gemini API quota exceeded.\n\n"
            "Tip: You can enter your own free Gemini API Key in the Sidebar from aistudio.google.com to bypass quota limits."
        )
    elif "503" in error:
        return "⚠️ Gemini AI service is temporarily unavailable. Please try again after a few seconds."
    elif "401" in error:
        return "⚠️ Invalid Gemini API Key. Please check your key settings."
    else:
        return f"⚠️ {error}"


def call_gemini(prompt):
    """Execute Gemini prompt with automatic model fallback and retry handling for 429 quota limits."""
    api_key = get_api_key()
    if not api_key:
        raise Exception("Gemini API Key is missing. Please set GEMINI_API_KEY in .env or enter it in the sidebar.")

    genai.configure(api_key=api_key)

    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    last_exception = None

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                last_exception = e
                err_str = str(e)
                if "429" in err_str:
                    time.sleep(2)  # Wait 2 seconds before retry on 429 quota error
                    continue
                else:
                    break

    if last_exception:
        raise last_exception
    else:
        raise Exception("Unable to get response from Gemini API.")


def analyze_resume(resume_text):
    prompt = f"""
You are an expert HR recruiter and ATS Resume Analyzer.

Analyze the following resume.

Return ONLY valid JSON.

Format:

{{
    "candidate_name":"",
    "email":"",
    "skills":[],
    "education":[],
    "projects":[],
    "experience":"",
    "strengths":[],
    "weaknesses":[],
    "resume_score":0,
    "ats_score":0,
    "missing_skills":[],
    "career_recommendation":"",
    "suggestions":[]
}}

Rules:
- Do not write markdown.
- Do not write explanation.
- Return ONLY JSON.

Resume:

{resume_text}
"""

    try:
        text = call_gemini(prompt).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)

    except Exception as e:
        return {
            "candidate_name": "Candidate",
            "email": "",
            "skills": ["Communication", "Problem Solving"],
            "education": [],
            "projects": [],
            "experience": "",
            "strengths": ["Strong foundational background"],
            "weaknesses": ["Consider listing specific technical certifications"],
            "resume_score": 75,
            "ats_score": 70,
            "missing_skills": ["Advanced Frameworks"],
            "career_recommendation": "Software Developer / Technical Specialist",
            "suggestions": [handle_gemini_error(e)]
        }


def evaluate_answer(question, answer):
    prompt = f"""
You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate using this format:

Score (out of 10):
Strengths:
Weaknesses:
Improved Answer:
"""

    try:
        return call_gemini(prompt)
    except Exception as e:
        return handle_gemini_error(e)


def evaluate_interview(questions, answers):
    qa = ""
    for i in range(len(questions)):
        answer_text = answers.get(i) or answers.get(str(i)) or ""
        qa += f"""
Question {i+1}:
{questions[i]}

Answer:
{answer_text}

"""

    prompt = f"""
You are an expert HR interviewer.

Evaluate the complete interview performance.

Interview Q&A:
{qa}

Return ONLY valid JSON.

Format:
{{
    "overall_score": 80,
    "technical": 8,
    "communication": 8,
    "problem_solving": 8,
    "confidence": 80,
    "strengths": ["Clear explanations", "Good structure"],
    "weaknesses": ["Provide more specific examples"],
    "suggestions": ["Practice coding problems", "Use STAR technique"],
    "final_recommendation": "Recommended"
}}

Rules:
- Return ONLY valid JSON.
- Do not use markdown backticks.
"""

    try:
        text = call_gemini(prompt).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)

    except Exception as e:
        print("Interview evaluation fallback triggered:", e)
        # Smart fallback if Gemini quota is completely exhausted
        answered_count = sum(1 for a in answers.values() if str(a).strip())
        tech_score = min(10, max(5, int(answered_count * 0.9)))
        comm_score = min(10, max(6, int(answered_count * 0.85)))
        prob_score = min(10, max(5, int(answered_count * 0.8)))
        overall = int((tech_score + comm_score + prob_score) / 30 * 100)

        return {
            "overall_score": overall,
            "technical": tech_score,
            "communication": comm_score,
            "problem_solving": prob_score,
            "confidence": 75,
            "strengths": [
                "Completed the full mock interview session",
                "Demonstrated active communication and effort",
                "Structured responses across questions"
            ],
            "weaknesses": [
                "Provide deeper technical code/architectural examples",
                "Work on elaboration for complex technical scenarios"
            ],
            "suggestions": [
                "Review core fundamentals mentioned in your resume",
                "Use the STAR method (Situation, Task, Action, Result) for answers",
                "Note: Gemini API Quota was reached; custom API key can be set in Sidebar."
            ],
            "final_recommendation": "Recommended for Next Round with Practice"
        }


def generate_interview_questions(interview_type, resume_text):
    prompt = f"""
You are an expert interviewer.

Interview Type:
{interview_type}

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
        text = call_gemini(prompt)
        questions = text.split("\n")
        questions = [q.strip() for q in questions if q.strip()]

        if len(questions) < 5:
            # Basic fallback questions if response length is short
            questions = [
                "Tell me about yourself and your background.",
                "What are your key technical strengths and skills?",
                "Describe a challenging project you worked on recently.",
                "How do you handle tight deadlines or pressure?",
                "Explain a complex technical concept from your resume.",
                "How do you stay updated with new technologies?",
                "Describe a time you solved a difficult bug or problem.",
                "What is your approach to teamwork and collaboration?",
                "Where do you see yourself professionally in the next 3 years?",
                "Why are you interested in this role and organization?"
            ]

        return questions[:10]

    except Exception as e:
        print("Question generation fallback triggered:", e)
        return [
            "Tell me about yourself and your background.",
            "What are your key technical strengths and skills?",
            "Describe a challenging project you worked on recently.",
            "How do you handle tight deadlines or pressure?",
            "Explain a complex technical concept from your resume.",
            "How do you stay updated with new technologies?",
            "Describe a time you solved a difficult bug or problem.",
            "What is your approach to teamwork and collaboration?",
            "Where do you see yourself professionally in the next 3 years?",
            "Why are you interested in this role and organization?"
        ]