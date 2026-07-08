import os

import pandas as pd
import streamlit as st
from keboola_streamlit import KeboolaStreamlit


TABLE_ID = "out.c-036-final-ads-jedox.ADS_CONTROLS"
DEFAULT_MEASURE = "REVENUES"
DEFAULT_SOURCE_PRIMARY = "VIT FINANCE"
DEFAULT_SOURCE_SECONDARY = "VIT FINANCE EXCEL"


if st.button("Back to Vitronic Hub"):
    st.switch_page("views/vitronic/hub.py")

st.markdown(
    "<h1 style='text-align: center; color: #1C83E1;'>Financial Checks</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        .fincheck-card {
            border: 1px solid #E1E8F5;
            border-radius: 8px;
            padding: 1rem;
            background: #FFFFFF;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
            min-height: 112px;
        }
        .fincheck-label {
            color: #64748B;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 0.35rem;
        }
        .fincheck-value {
            color: #0F172A;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .fincheck-note {
            color: #64748B;
            font-size: 0.86rem;
            margin-top: 0.35rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_text(value):
    return str(value).strip().upper()


def sorted_options(df, column):
    if column not in df.columns:
        return []
    values = df[column].dropna().astype(str).str.strip()
    values = values[values != ""].unique().tolist()
    return sorted(values)


def default_source(values, preferred, fallback_contains):
    normalized = {normalize_text(value): value for value in values}
    if normalize_text(preferred) in normalized:
        return normalized[normalize_text(preferred)]

    for value in values:
        normalized_value = normalize_text(value)
        if all(part in normalized_value for part in fallback_contains):
            return value

    return values[0] if values else None


def format_number(value):
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}".replace(",", " ")


def render_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="fincheck-card">
            <div class="fincheck-label">{label}</div>
            <div class="fincheck-value">{value}</div>
            <div class="fincheck-note">{note}</div>
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


kbc_url = get_config_value("KBC_URL", default="https://connection.europe-west3.gcp.keboola.com")
kbc_token = get_config_value("EDITOR_TOKEN", "KBC_TOKEN", "KBC_STORAGE_TOKEN", "STORAGE_TOKEN")

if not kbc_token:
    st.error(
        "Missing Keboola Storage API token. Add a secret or environment variable named "
        "EDITOR_TOKEN in the Keboola app configuration."
    )
    st.stop()

keboola = KeboolaStreamlit(
    root_url=kbc_url,
    token=kbc_token,
)


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

controls_df["BALANCE_AMOUNT"] = pd.to_numeric(controls_df["BALANCE_AMOUNT"], errors="coerce")
controls_df["BALANCE_AMOUNT_YTD"] = pd.to_numeric(controls_df["BALANCE_AMOUNT_YTD"], errors="coerce")
controls_df["CODE_PERIOD_VALUE"] = controls_df["CODE_PERIOD_VALUE"].astype(str)

st.divider()

with st.container(border=True):
    st.caption("Filters")
    col_cbs, col_company, col_period, col_currency = st.columns(4)

    with col_cbs:
        selected_cbs = st.multiselect("CBS", sorted_options(controls_df, "CBS"))
    with col_company:
        selected_company = st.multiselect(
            "Group company",
            sorted_options(controls_df, "GROUP_COMPANY"),
        )
    with col_period:
        selected_period = st.multiselect(
            "Period",
            sorted_options(controls_df, "CODE_PERIOD_VALUE"),
        )
    with col_currency:
        selected_currency = st.multiselect(
            "Currency",
            sorted_options(controls_df, "CURRENCY"),
        )

filtered_df = controls_df.copy()
if selected_cbs:
    filtered_df = filtered_df[filtered_df["CBS"].astype(str).isin(selected_cbs)]
if selected_company:
    filtered_df = filtered_df[filtered_df["GROUP_COMPANY"].astype(str).isin(selected_company)]
if selected_period:
    filtered_df = filtered_df[filtered_df["CODE_PERIOD_VALUE"].astype(str).isin(selected_period)]
if selected_currency:
    filtered_df = filtered_df[filtered_df["CURRENCY"].astype(str).isin(selected_currency)]

revenue_df = filtered_df[
    filtered_df["CONTROL_MEASURE"].astype(str).map(normalize_text) == DEFAULT_MEASURE
].copy()

source_options = sorted_options(revenue_df, "CODE_SOURCE")
if not source_options:
    st.warning("No revenues found for the selected filters.")
    st.stop()

primary_default = default_source(source_options, DEFAULT_SOURCE_PRIMARY, ["FINANCE"])
secondary_default = default_source(source_options, DEFAULT_SOURCE_SECONDARY, ["FINANCE", "EXCEL"])

source_col_1, source_col_2, amount_col = st.columns([2, 2, 1])
with source_col_1:
    primary_source = st.selectbox(
        "Primary source",
        source_options,
        index=source_options.index(primary_default) if primary_default in source_options else 0,
    )
with source_col_2:
    secondary_source = st.selectbox(
        "Comparison source",
        source_options,
        index=source_options.index(secondary_default) if secondary_default in source_options else 0,
    )
with amount_col:
    amount_field = st.selectbox(
        "Amount",
        ["BALANCE_AMOUNT", "BALANCE_AMOUNT_YTD"],
        format_func=lambda value: "Monthly" if value == "BALANCE_AMOUNT" else "YTD",
    )

if primary_source == secondary_source:
    st.warning("Select two different sources to compare revenues.")
    st.stop()

comparison_df = revenue_df[revenue_df["CODE_SOURCE"].isin([primary_source, secondary_source])]
summary_df = (
    comparison_df.groupby("CODE_SOURCE", dropna=False)[amount_field]
    .sum()
    .reindex([primary_source, secondary_source])
    .fillna(0)
)

primary_total = summary_df.loc[primary_source]
secondary_total = summary_df.loc[secondary_source]
difference = primary_total - secondary_total
difference_pct = difference / secondary_total if secondary_total else 0

st.subheader("Revenues control")
card_1, card_2, card_3, card_4 = st.columns(4)
with card_1:
    render_card(primary_source, format_number(primary_total), amount_field)
with card_2:
    render_card(secondary_source, format_number(secondary_total), amount_field)
with card_3:
    render_card("Difference", format_number(difference), "Primary minus comparison")
with card_4:
    render_card("Difference %", f"{difference_pct:.2%}", "Against comparison source")

st.divider()

chart_df = (
    comparison_df.groupby(["CODE_PERIOD_VALUE", "CODE_SOURCE"], dropna=False)[amount_field]
    .sum()
    .reset_index()
    .pivot(index="CODE_PERIOD_VALUE", columns="CODE_SOURCE", values=amount_field)
    .reindex(columns=[primary_source, secondary_source])
    .fillna(0)
    .sort_index()
)

st.caption("Revenue trend by period")
st.bar_chart(chart_df, use_container_width=True)

detail_df = chart_df.copy()
detail_df["Difference"] = detail_df[primary_source] - detail_df[secondary_source]
detail_df["Difference %"] = detail_df.apply(
    lambda row: row["Difference"] / row[secondary_source] if row[secondary_source] else 0,
    axis=1,
)

st.caption("Detail by period")
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
)
