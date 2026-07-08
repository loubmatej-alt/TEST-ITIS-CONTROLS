import streamlit as st

st.title("Itis Hub")

if st.button("⬅ Back to Home"):
    st.switch_page("views/home.py")

st.divider()

st.subheader("Available Processes")
st.write("Select a process to run:")

# Mřížka 2x3 pomocí 3 sloupců
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### Mapping")
        st.caption("Manage unmapped accounts.")
        if st.button("Open", key="btn_unmapped", use_container_width=True, type="primary"):
            st.switch_page("views/itis/process1.py")

    with st.container(border=True):
        st.markdown("### Fin. Checks")
        st.caption("Test of key indicators")
        if st.button("Open", key="btn_fincheck", use_container_width=True, type="primary"):
            st.switch_page("views/itis/process1.py")   


with col2:
    with st.container(border=True):
        st.markdown("### Flows")
        st.caption("Execute Keboola flows")
        if st.button("Open", key="btn_flows", use_container_width=True, type="primary"):
            st.switch_page("views/itis/process1.py")    

    with st.container(border=True):
        st.markdown("### Glossary")
        st.caption("Editor for business glossary")
        if st.button("Open", key="btn_p6", use_container_width=True, type="primary"):
            st.switch_page("views/itis/process1.py")    


with col3:
    with st.container(border=True):
        st.markdown("### Accruals")
        st.caption("Monthly acrruals check")
        if st.button("Open", key="btn_accruals", use_container_width=True, type="primary"):
            st.switch_page("views/itis/process1.py")   

    with st.container(border=True):
        st.markdown("### HR data")
        st.caption("Reporting and exports for HR")
        st.button("Open", key="btn_p5", use_container_width=True, disabled=True)