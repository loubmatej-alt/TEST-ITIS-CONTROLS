import streamlit as st
import requests
import time
import os


if st.button("⬅ Back to Vitronic Hub"):
    st.switch_page("views/vitronic/hub.py")

# --- KONFIGURACE ---
# Flow IDs need to be replaced with real IDs from Keboola
VIT_FLOWS = {
    "Full Update": "01kt3y13xczy324bqjf8grc4sq",
    "VIT CRM OI": "01kt46e7x2gn7zct8f59vtdtjn",
    "VIT AR": "ccc"
}

KBC_TOKEN = st.secrets["EDITOR_TOKEN"]
KBC_URL = st.secrets.get("KBC_URL", "https://connection.europe-west3.gcp.keboola.com")

# --- DEFINICE FUNKCÍ ---
def trigger_flow(flow_id):
    queue_url = KBC_URL.replace("connection", "queue")
    api_url = f"{queue_url}/jobs"
    headers = {
        "X-StorageApi-Token": KBC_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "component": "keboola.orchestrator",
        "mode": "run",
        "config": flow_id
    }
    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("id")

def wait_for_job(job_id):
    queue_url = KBC_URL.replace("connection", "queue")
    job_url = f"{queue_url}/jobs/{job_id}"
    headers = {"X-StorageApi-Token": KBC_TOKEN}
    
    terminal_states = ["success", "error", "terminated", "cancelled"]
    
    while True:
        res = requests.get(job_url, headers=headers)
        res.raise_for_status()
        job_data = res.json()
        status = job_data.get("status")
        
        if status in terminal_states:
            return status
        time.sleep(2)

# --- UI ---
st.markdown(
    "<h1 style='text-align: center; color: #1C83E1;'>Keboola flows</h1>", 
    unsafe_allow_html=True
)


st.divider()

st.subheader("Available Flows")
st.write("Select a process to run:")



for flow_name, flow_id in VIT_FLOWS.items():
    # Změna: Tlačítko dostane 33 % šířky, text 66 %
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Tlačítko si jen uložíme do proměnné, abychom věděli, jestli bylo stisknuto
        run_pressed = st.button(f"▶ {flow_name}", key=flow_id, use_container_width=True)
    with col2:
        st.write(f"Click to start orchestration for {flow_name}")
        
    # Změna: Vlastní spuštění a logování je teď MIMO sloupce, pod nimi.
    # Díky tomu získá status kontejner celou šířku obrazovky!
    if run_pressed:
        try:
            with st.status(f"Syncing {flow_name}...", expanded=True) as status_container:
                status_container.write("🚀 Triggering flow in Keboola...")
                job_id = trigger_flow(flow_id)
                status_container.write(f"⏳ Job {job_id} is running, waiting for completion...")
                final_status = wait_for_job(job_id)
                if final_status == "success":
                    status_container.update(label=f"✅ {flow_name} completed!", state="complete", expanded=False)
                else:
                    status_container.update(label=f"❌ {flow_name} failed: {final_status}", state="error")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            
    # Přidáme lehkou čáru pro vizuální oddělení jednotlivých flow
    st.divider()