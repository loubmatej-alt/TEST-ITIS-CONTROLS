import os
import re

import pandas as pd
import streamlit as st
from keboola_streamlit import KeboolaStreamlit


TABLE_ID = "out.c-036-final-ads-jedox.ADS_CONTROLS"
CONTROL_MEASURE = "REVENUES"
PRIMARY_SOURCE_NAME = "VIT FINANCE"
SECONDARY_SOURCE_NAME = "VIT FINANCE EXCEL"
DEFAULT_CURRENCY = "EUR"
DEFAULT_CBS_VALUES = {"", "CBS1", "CBS2 ADJ"}


if st.button("Back to Vitronic Hub"):
    st.switch_page("views/vitronic/hub.py")

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            max-width: 1180px;
        }
        .fincheck-hero {
            border: 1px solid #D8E4F2;
            border-radius: 8px;
            padding: 1.2rem 1.35rem;
            background: linear-gradient(135deg, #F8FBFF 0%, #EEF6FF 100%);
            margin-bottom: 1rem;
        }
        .fincheck-title {
            color: #102033;
            font-size: 2rem;
            font-weight: 760;
            line-height: 1.15;
            margin: 0;
        }
        .fincheck-subtitle {
            color: #526174;
            font-size: 0.95rem;
            margin-top: 0.35rem;
        }
        .scope-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.9rem;
        }
        .scope-pill {
            border: 1px solid #CFE0F3;
            background: #FFFFFF;
            color: #1F3B57;
            border-radius: 999px;
            padding: 0.28rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .kpi-card {
            border: 1px solid #DDE7F3;
            border-radius: 8px;
            background: #FFFFFF;
            padding: 1rem;
            min-height: 132px;
            box-shadow: 0 1px 6px rgba(16, 32, 51, 0.06);
        }
        .kpi-label {
            color: #69788A;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 0.45rem;
        }
        .kpi-value {
            color: #102033;
            font-size: 1.75rem;
            font-weight: 760;
            line-height: 1.15;
            word-break: break-word;
        }
        .kpi-note {
            color: #69788A;
            font-size: 0.84rem;
            margin-top: 0.45rem;
        }
        .status-ok .kpi-value { color: #178A4C; }
        .status-warn .kpi-value { color: #B45309; }
        .section-title {
            color: #102033;
            font-size: 1.05rem;
            font-weight: 740;
            margin: 0.7rem 0 0.4rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def format_number(value):
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}".replace(",", " ")


def format_pct(value):
    if pd.isna(value):
        return "-"
    return f"{value:.2%}"


def render_kpi(label, value, note="", status=None):
    status_class = f" status-{status}" if status else ""
    st.markdown(
        f"""
        <div class="kpi-card{status_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_config_value(*names, default=None):
    for name in names:
        value = st.secrets.get(name) or os.environ.get(name)
        if value:
            return value
    return default


def find_source(values, preferred, required_terms, excluded_terms=None):
    excluded_terms = excluded_terms or []
    normalized = {normalize_text(value): value for value in values}
    preferred_norm = normalize_text(preferred)
    if preferred_norm in normalized:
        return normalized[preferred_norm]

    for value in values:
        value_norm = normalize_text(value)
        if all(term in value_norm for term in required_terms) and not any(
            term in value_norm for term in excluded_terms
        ):
            return value
    return None


def show_empty_state(title, detail, debug_steps=None, df=None):
    st.warning(title)
    st.caption(detail)
    if debug_steps:
        st.dataframe(pd.DataFrame(debug_steps), use_container_width=True, hide_index=True)
    if df is not None and not df.empty:
        st.caption("Available values in the current data slice")
        diagnostics = []
        for column in ["CBS", "GROUP_COMPANY", "CODE_PERIOD_VALUE", "CURRENCY", "CONTROL_MEASURE", "CODE_SOURCE"]:
            if column in df.columns:
                values = sorted(df[column].fillna("").astype(str).str.strip().unique().tolist())
                diagnostics.append({"Column": column, "Values": ", ".join(values[:30])})
        st.dataframe(pd.DataFrame(diagnostics), use_container_width=True, hide_index=True)
    st.stop()


kbc_url = get_config_value("KBC_URL", default="https://connection.europe-west3.gcp.keboola.com")
kbc_token = get_config_value("EDITOR_TOKEN", "KBC_TOKEN", "KBC_STORAGE_TOKEN", "STORAGE_TOKEN")

if not kbc_token:
    st.error(
        "Missing Keboola Storage API token. Add a secret or environment variable named "
        "EDITOR_TOKEN in the Keboola app configuration."
    )
    st.stop()

keboola = KeboolaStreamlit(root_url=kbc_url, token=kbc_token)


@st.cache_data(ttl=600)
def load_controls():
    return keboola.read_table(TABLE_ID)


with st.spinner("Loading ADS controls from Keboola..."):
    try:
        controls_df = load_controls()
    except Exception as exc:
        st.error(f"Could not load table {TABLE_ID}: {exc}")
        st.stop()

required_columns = {
    "CBS",
    "GROUP_COMPANY",
    "CODE_PERIOD_VALUE",
    "CURRENCY",
    "CONTROL_MEASURE",
    "CODE_SOURCE",
    "BALANCE_AMOUNT",
    "BALANCE_AMOUNT_YTD",
}
missing_columns = sorted(required_columns - set(controls_df.columns))
if missing_columns:
    st.error("Missing required columns: " + ", ".join(missing_columns))
    st.stop()

controls_df = controls_df.copy()
controls_df["BALANCE_AMOUNT"] = pd.to_numeric(controls_df["BALANCE_AMOUNT"], errors="coerce").fillna(0)
controls_df["BALANCE_AMOUNT_YTD"] = pd.to_numeric(controls_df["BALANCE_AMOUNT_YTD"], errors="coerce").fillna(0)
controls_df["CODE_PERIOD_VALUE"] = controls_df["CODE_PERIOD_VALUE"].fillna("").astype(str).str.strip()
controls_df["_CBS_NORM"] = controls_df["CBS"].map(normalize_text)
controls_df["_GROUP_COMPANY_NORM"] = controls_df["GROUP_COMPANY"].map(normalize_text)
controls_df["_CURRENCY_NORM"] = controls_df["CURRENCY"].map(normalize_text)
controls_df["_CONTROL_MEASURE_NORM"] = controls_df["CONTROL_MEASURE"].map(normalize_text)

period_options = sorted(
    controls_df.loc[
        controls_df["CODE_PERIOD_VALUE"].str.match(r"^2026(0[1-9]|1[0-2])$", na=False),
        "CODE_PERIOD_VALUE",
    ].unique()
)
if not period_options:
    show_empty_state(
        "No 2026 periods found in ADS_CONTROLS.",
        "The MVP period selector only allows months from 2026.",
        df=controls_df,
    )

default_period = period_options[-1]

st.markdown(
    f"""
    <div class="fincheck-hero">
        <div class="fincheck-title">Financial Checks</div>
        <div class="fincheck-subtitle">Revenue reconciliation between finance source and Excel control source.</div>
        <div class="scope-row">
            <span class="scope-pill">GROUP_COMPANY: V0*</span>
            <span class="scope-pill">Currency: {DEFAULT_CURRENCY}</span>
            <span class="scope-pill">CBS: blank, CBS1, CBS2 ADJ</span>
            <span class="scope-pill">Measure: {CONTROL_MEASURE}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

period_col, refresh_col = st.columns([3, 1])
with period_col:
    selected_period = st.selectbox(
        "Period",
        period_options,
        index=period_options.index(default_period),
        help="MVP allows only 2026 monthly periods.",
    )
with refresh_col:
    st.write("")
    st.write("")
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

steps = []
base_df = controls_df.copy()
steps.append({"Step": "Loaded rows", "Rows": len(base_df)})

base_df = base_df[base_df["_GROUP_COMPANY_NORM"].str.match(r"^V0", na=False)]
steps.append({"Step": "GROUP_COMPANY starts with V0", "Rows": len(base_df)})

base_df = base_df[base_df["_CURRENCY_NORM"] == DEFAULT_CURRENCY]
steps.append({"Step": f"CURRENCY = {DEFAULT_CURRENCY}", "Rows": len(base_df)})

base_df = base_df[base_df["_CBS_NORM"].isin(DEFAULT_CBS_VALUES)]
steps.append({"Step": "CBS blank/CBS1/CBS2 ADJ", "Rows": len(base_df)})

base_df = base_df[base_df["_CONTROL_MEASURE_NORM"] == CONTROL_MEASURE]
steps.append({"Step": f"CONTROL_MEASURE = {CONTROL_MEASURE}", "Rows": len(base_df)})

if base_df.empty:
    show_empty_state(
        "No revenue rows found for the default dashboard scope.",
        "Check the diagnostic table below. One of the default filters does not match the current ADS_CONTROLS data.",
        debug_steps=steps,
        df=controls_df,
    )

source_options = sorted(base_df["CODE_SOURCE"].fillna("").astype(str).str.strip().unique().tolist())
primary_source = find_source(source_options, PRIMARY_SOURCE_NAME, ["FINANCE"], ["EXCEL"])
secondary_source = find_source(source_options, SECONDARY_SOURCE_NAME, ["FINANCE", "EXCEL"])

if not primary_source or not secondary_source:
    show_empty_state(
        "Could not identify both revenue sources.",
        "Expected one finance source and one Excel control source in CODE_SOURCE after applying the default scope.",
        debug_steps=steps + [{"Step": "Available CODE_SOURCE", "Rows": ", ".join(source_options)}],
        df=base_df,
    )

current_df = base_df[base_df["CODE_PERIOD_VALUE"] == selected_period]
if current_df.empty:
    show_empty_state(
        f"No revenue rows found for period {selected_period}.",
        "Try another 2026 period or check whether ADS_CONTROLS contains the default scope for this month.",
        debug_steps=steps + [{"Step": f"CODE_PERIOD_VALUE = {selected_period}", "Rows": 0}],
        df=base_df,
    )

current_sources = current_df[current_df["CODE_SOURCE"].isin([primary_source, secondary_source])]
summary = (
    current_sources.groupby("CODE_SOURCE", dropna=False)["BALANCE_AMOUNT_YTD"]
    .sum()
    .reindex([primary_source, secondary_source])
    .fillna(0)
)

primary_total = summary.loc[primary_source]
secondary_total = summary.loc[secondary_source]
difference = primary_total - secondary_total
difference_pct = difference / secondary_total if secondary_total else pd.NA
status_ok = abs(difference) < 1

st.markdown('<div class="section-title">Revenue Control Summary</div>', unsafe_allow_html=True)
kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
with kpi_1:
    render_kpi(primary_source, format_number(primary_total), f"YTD revenue, {selected_period}")
with kpi_2:
    render_kpi(secondary_source, format_number(secondary_total), f"YTD control, {selected_period}")
with kpi_3:
    render_kpi("Difference", format_number(difference), "Finance minus Excel")
with kpi_4:
    render_kpi(
        "Status",
        "OK" if status_ok else "Check",
        f"Variance {format_pct(difference_pct)}",
        status="ok" if status_ok else "warn",
    )

trend_df = (
    base_df[base_df["CODE_SOURCE"].isin([primary_source, secondary_source])]
    .groupby(["CODE_PERIOD_VALUE", "CODE_SOURCE"], dropna=False)["BALANCE_AMOUNT_YTD"]
    .sum()
    .reset_index()
)
trend_df = trend_df[trend_df["CODE_PERIOD_VALUE"].isin(period_options)]
chart_df = (
    trend_df.pivot(index="CODE_PERIOD_VALUE", columns="CODE_SOURCE", values="BALANCE_AMOUNT_YTD")
    .reindex(columns=[primary_source, secondary_source])
    .fillna(0)
    .sort_index()
)
chart_df["Difference"] = chart_df[primary_source] - chart_df[secondary_source]

st.divider()
chart_col, table_col = st.columns([1.45, 1])
with chart_col:
    st.markdown('<div class="section-title">2026 YTD Trend</div>', unsafe_allow_html=True)
    st.line_chart(chart_df[[primary_source, secondary_source]], use_container_width=True)

with table_col:
    st.markdown('<div class="section-title">Period Detail</div>', unsafe_allow_html=True)
    detail_df = chart_df.copy()
    detail_df["Difference %"] = detail_df.apply(
        lambda row: row["Difference"] / row[secondary_source] if row[secondary_source] else pd.NA,
        axis=1,
    )
    st.dataframe(
        detail_df.style.format(
            {
                primary_source: "{:,.0f}",
                secondary_source: "{:,.0f}",
                "Difference": "{:,.0f}",
                "Difference %": "{:.2%}",
            }
        ),
        use_container_width=True,
        height=330,
    )

with st.expander("Dashboard scope diagnostics"):
    scope = pd.DataFrame(
        [
            {"Filter": "GROUP_COMPANY", "Applied value": "starts with V0", "Matched rows": steps[1]["Rows"]},
            {"Filter": "CURRENCY", "Applied value": DEFAULT_CURRENCY, "Matched rows": steps[2]["Rows"]},
            {"Filter": "CBS", "Applied value": "blank, CBS1, CBS2 ADJ", "Matched rows": steps[3]["Rows"]},
            {"Filter": "CONTROL_MEASURE", "Applied value": CONTROL_MEASURE, "Matched rows": steps[4]["Rows"]},
            {"Filter": "Primary source", "Applied value": primary_source, "Matched rows": len(current_df[current_df["CODE_SOURCE"] == primary_source])},
            {"Filter": "Comparison source", "Applied value": secondary_source, "Matched rows": len(current_df[current_df["CODE_SOURCE"] == secondary_source])},
        ]
    )
    st.dataframe(scope, use_container_width=True, hide_index=True)
