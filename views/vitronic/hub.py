import streamlit as st

if st.button("⬅ Back to Home"):
    st.switch_page("views/home.py")

st.markdown(
    "<h1 style='text-align: center; color: #1C83E1;'>Vitronic Hub</h1>", 
    unsafe_allow_html=True
)

# col_left, col_center, col_right = st.columns([3, 1, 3])
# with col_center:
#    st.title(":blue[Vitronic Hub]")



hide_sidebar_css = """
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
</style>
"""
st.markdown(hide_sidebar_css, unsafe_allow_html=True)



st.divider()

st.subheader("Available Processes")

# Mřížka 2x3 pomocí 3 sloupců
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### Mapping")
        st.caption("Manage unmapped accounts.")
        if st.button("Open", key="btn_unmapped", use_container_width=True, type="primary"):
            st.switch_page("views/vitronic/accounts_unmapped.py")

    with st.container(border=True):
        st.markdown("### Fin. Checks")
        st.caption("Test of key indicators")
        if st.button("Open", key="btn_fincheck", use_container_width=True, type="primary"):
            st.switch_page("views/vitronic/fincheck.py")   


with col2:
    with st.container(border=True):
        st.markdown("### Flows")
        st.caption("Execute Keboola flows")
        if st.button("Open", key="btn_flows", use_container_width=True, type="primary"):
            st.switch_page("views/vitronic/flows.py")    

    with st.container(border=True):
        st.markdown("### Glossary")
        st.caption("Editor for business glossary")
        if st.button("Open", key="btn_p6", use_container_width=True, type="primary"):
            st.switch_page("views/vitronic/glossary.py")    


with col3:
    with st.container(border=True):
        st.markdown("### Accruals")
        st.caption("Monthly acrruals check")
        if st.button("Open", key="btn_accruals", use_container_width=True, type="primary"):
            st.switch_page("views/vitronic/accruals.py")   

    with st.container(border=True):
        st.markdown("### HR data")
        st.caption("Reporting and exports for HR")
        st.button("Open", key="btn_p5", use_container_width=True, disabled=True)