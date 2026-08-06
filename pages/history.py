import streamlit as st
import pandas as pd
from database.database import get_interview_history

# Login Check
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Please login first.")
    st.switch_page("pages/login.py")

st.title("📜 Interview History")

history = get_interview_history(st.session_state.email)
st.write("Logged in Email:", st.session_state.email)
#st.write(history)

if not history:
    st.info("No interview history found.")
else:

    scores = []

    for interview in history:
        try:
            scores.append(float(interview[1]))
        except:
            pass
    #st.write(scores)

    col1, col2, col3, col4 = st.columns(4)

    completed = len(scores)

    with col1:
        st.metric("📄 Total Interviews", len(history))
    with col2:
        pass
        st.metric("⭐ Average Score", f"{sum(scores)/len(scores):.1f}")

    with col3:
        st.metric("🏆 Best Score", max(scores))

    chart_data = pd.DataFrame({
        "Interview": range(1, len(scores) + 1),
        "Score": scores
    })

    with col4:
        st.metric("✅ Completed", completed)

    st.subheader("📈 Performance Trend")
    st.caption("This graph shows the scores of completed interviews only.")
    st.line_chart(chart_data.set_index("Interview"))

    for interview in history:

        st.markdown("---")

        st.write("📅 Date:", interview[0])
        st.write("📊 Score:", interview[1])

        with st.expander("View Report"):
            st.markdown(interview[2])