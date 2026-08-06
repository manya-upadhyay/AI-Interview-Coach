import streamlit as st
from database.database import register_user

st.title("📝 Sign Up")

name = st.text_input("Full Name")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Register"):
    if register_user(name, email, password):
        st.success("Registration Successful ✅")
    else:
        st.error("Email already exists!")