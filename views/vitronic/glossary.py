
import streamlit as st
from keboola_streamlit import KeboolaStreamlit

st.set_page_config(layout="wide", page_title="Glossary")

# --- MAGIE PRO RESET: Vytvoříme počítadlo pro klíč ---
if "editor_key" not in st.session_state:
    st.session_state["editor_key"] = 0
# -----------------------------------------------------

st.markdown("<h1 style='text-align: center; color: #1C83E1;'>Glossary Editor</h1>", unsafe_allow_html=True)
st.divider()
st.caption("Edit the selected codelist. Changes need to be saved using the button below.")

# 1. Inicializace klienta
keboola = KeboolaStreamlit(
    root_url=st.secrets.get("KBC_URL", "https://connection.europe-west3.gcp.keboola.com"),
    token=st.secrets["EDITOR_TOKEN"]
)

table_id = "out.c-892-test-for-data-app-2.DC_FIN_ACCOUNT_MGMT_TEST"

# 2. Cachované načtení dat
@st.cache_data(ttl=600)
def load_data():
    return keboola.read_table(table_id)

with st.spinner("Loading data from Keboola..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# 3. Interaktivní editor s DYNAMICKÝM KLÍČEM
edited_df = st.data_editor(
    df, 
    key=f"glossary_editor_{st.session_state['editor_key']}", # Zde se klíč dynamicky mění
    use_container_width=True, 
    num_rows="dynamic", 
    height=500
)

st.divider()

# 4. Tlačítka
col1, col2 = st.columns([1, 3])

with col1:
    if st.button("💾 Save changes to Keboola", type="primary", use_container_width=True):
        with st.spinner("Saving data..."):
            try:
                keboola.write_table(table_id=table_id, df=edited_df, is_incremental=False)
                st.cache_data.clear() 
                
                # Pro jistotu změníme klíč i po uložení
                st.session_state["editor_key"] += 1 
                
                st.success("🎉 Data was successfully saved!")
                st.rerun() 
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("🔄 Reset table", type="secondary", use_container_width=True):
        with st.spinner("Restoring original data..."):
            st.cache_data.clear() # Smaže stará data z paměti
            
            # TADY JE TEN TRIK: Zvýšíme číslo klíče.
            # Streamlit zahodí starou tabulku a vytvoří úplně novou.
            st.session_state["editor_key"] += 1
            
            st.rerun()