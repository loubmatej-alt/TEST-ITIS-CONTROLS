import streamlit as st
from keboola_streamlit import KeboolaStreamlit

if st.button("⬅ Back to Vitronic Hub"):
    st.switch_page("views/vitronic/hub.py")

st.markdown("<h1 style='text-align: center; color: #1C83E1;'>Unmapped Accounts</h1>", unsafe_allow_html=True)


st.divider()

st.write("Accounts that are not mapped:")

# 1. Inicializace speciálního Streamlit klienta
keboola = KeboolaStreamlit(
    root_url=st.secrets.get("KBC_URL", "https://connection.europe-west3.gcp.keboola.com"),
    token=st.secrets["EDITOR_TOKEN"]
)

table_id = "out.c-016-idl-data.FT_FIN_IDL_VIT_ACCOUNTS_NOT_MAPPED"

# 2. Přímé načtení dat do DataFramu
with st.spinner("Loading data..."):
    df = keboola.read_table(table_id)
    st.dataframe(df, use_container_width=True)

st.divider()  

st.write("Edit mappping:")

sharepoint_url = "https://skytollas.sharepoint.com/:x:/s/erp-itis/IQD4MoYtWQMkQ7--tjfv_bMfAduVNrLgR_18ah8aV0KSCJE?e=Vy9vmG"
st.link_button("📊 Excel with account mapping (Sharepoint)", sharepoint_url)
