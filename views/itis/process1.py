import streamlit as st

st.title("Itis - Process 1")
if st.button("⬅ Back to Itis Hub"):
    st.switch_page("views/itis/hub.py")

st.divider()

st.write("Logic for the first Itis process goes here.")
# Insert specific code for this process here (pandas, charts, etc.)
st.info("Process workspace is ready.")