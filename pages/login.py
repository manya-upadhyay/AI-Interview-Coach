import streamlit as st
from database.database import login_user

st.session_state.setdefault("logged_in", False)

st.title("🔐 Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):

    user = login_user(email, password)

    if user:

        st.session_state.logged_in = True
        st.session_state.user = user[1]
        st.session_state.email = user[2]

        st.success(f"Welcome {user[1]} 🎉")

        st.switch_page("pages/dashboard.py")


    else:
        st.error("Invalid Email or Password")