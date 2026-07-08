import streamlit as st

st.set_page_config(page_title="Business Portal", layout="centered")

# Define pages and their file paths
home = st.Page("views/home.py", title="Home", default=True, icon="🟦")


# Pages - Vitronic
# Added 'url_path' to prevent routing collisions
vitronic_accounts_unmapped = st.Page("views/vitronic/accounts_unmapped.py", title="Unmapped accounts", icon="▪️", url_path="vitronic_accounts_unmapped")
vitronic_flows = st.Page("views/vitronic/flows.py", title="Flows", icon="▪️", url_path="vitronic_flows")
vitronic_hub = st.Page("views/vitronic/hub.py", title="Vitronic Hub", icon="▪️", url_path="vitronic_hub")
vitronic_accruals = st.Page("views/vitronic/accruals.py", title="Accruals", icon="▪️", url_path="vitronic_accruals")
vitronic_fincheck = st.Page("views/vitronic/fincheck.py", title="Financial Checks", icon="▪️", url_path="vitronic_fincheck")
vitronic_glossary = st.Page("views/vitronic/glossary.py", title="Glossary", icon="▪️", url_path="vitronic_glossary")

# Pages - Itis
# Added 'url_path' to prevent routing collisions
itis_hub = st.Page("views/itis/hub.py", title="Itis Hub", icon="▫️", url_path="itis_hub")
itis_process1 = st.Page("views/itis/process1.py", title="Itis: Process 1", icon="▫️", url_path="itis_process1")
itis_process2 = st.Page("views/itis/process1.py", title="Itis: Process 2", icon="▫️", url_path="itis_process2")
itis_process3 = st.Page("views/itis/process1.py", title="Itis: Process 3", icon="▫️", url_path="itis_process3")
itis_process4 = st.Page("views/itis/process1.py", title="Itis: Process 4", icon="▫️", url_path="itis_process4")
itis_process5 = st.Page("views/itis/process1.py", title="Itis: Process 5", icon="▫️", url_path="itis_process5")

# Register navigation into logical sections
pg = st.navigation({
    "Start": [home],
    "Vitronic": [vitronic_hub,vitronic_accounts_unmapped, vitronic_flows, vitronic_glossary,vitronic_accruals, vitronic_fincheck ],    
    "ITIS": [itis_hub, itis_process1, itis_process2, itis_process3, itis_process4, itis_process5],
})

# Run the navigation
pg.run()