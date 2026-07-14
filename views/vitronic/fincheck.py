import os
import re

import pandas as pd
import streamlit as st
from keboola_streamlit import KeboolaStreamlit


# =============================================================================
# Configuration
# =============================================================================
# Source table prepared in Keboola. It is expected to have one row per 2026 period
# and ready-made columns for IDL value, Excel value, and CHECK status per metric.
TABLE_ID = "out.c-036-final-ads-jedox.ADS_CONTROLS_2026"
MONTHLY_YTD_TABLE_ID = "out.c-036-final-ads-jedox.ADS_CONTROLS_M_YTD_2026"
BALANCE_SHEET_TABLE_ID = "out.c-036-final-ads-jedox.ADS_CONTROLS_BS_2026"
OK_TOLERANCE = 1
POWER_BI_DETAIL_URL = "https://app.powerbi.com/groups/20d8270f-2eb5-463c-a99b-e63b7f7fbe8a/reports/e51d703b-a94a-4167-a664-0fde0315f0c8/a1be24ae0c7faff0bccb?experience=power-bi"


if st.button("< Back to Vitronic Hub", key="back_to_vitronic_hub", type="secondary"):
    st.switch_page("views/vitronic/hub.py")


# =============================================================================
# Page Styling
# =============================================================================
# Page-local CSS. Keeping this here makes the dashboard self-contained and avoids
# touching the rest of the Streamlit app styling.
st.markdown(
    """
    <style>
        .block-container { padding-top: 3.4rem; max-width: 1180px; }
        .fc-hero {
            border: 1px solid #D7E1EC; border-radius: 8px; padding: 1.15rem 1.25rem;
            background: #F8FAFC; margin-bottom: 1rem;
        }
        .fc-title { color: #132033; font-size: 1.9rem; font-weight: 760; line-height: 1.15; margin: 0; }
        .fc-subtitle { color: #5D6B7B; font-size: 0.94rem; margin-top: 0.35rem; }
        .fc-pill-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.85rem; }
        .fc-pill {
            border: 1px solid #D7E1EC; background: #FFFFFF; color: #31465C; border-radius: 999px;
            padding: 0.28rem 0.72rem; font-size: 0.8rem; font-weight: 650;
        }
        .fc-status-band { border-radius: 8px; padding: 0.95rem 1rem; margin: 0.6rem 0 1rem 0; border: 1px solid; }
        .fc-ok { background: #ECFDF3; border-color: #B7E4C7; color: #126C3A; }
        .fc-bad { background: #FEF2F2; border-color: #F4C7C7; color: #9F1D1D; }
        .fc-incomplete { background: #FFFBEB; border-color: #F6D58D; color: #8A5A00; }
        .fc-status-title { font-size: 1.05rem; font-weight: 760; margin-bottom: 0.2rem; }
        .fc-status-note { font-size: 0.88rem; opacity: 0.88; }
        .metric-card {
            border: 1px solid #DDE6F1; border-radius: 8px; background: #FFFFFF; padding: 1rem;
            min-height: 124px; box-shadow: 0 1px 6px rgba(15, 23, 42, 0.06);
        }
        .metric-card.ok { border-left: 5px solid #22A06B; }
        .metric-card.bad { border-left: 5px solid #E55353; }
        .metric-card.incomplete { border-left: 5px solid #D99A1E; }
        .metric-title { color: #132033; font-size: 1.05rem; font-weight: 760; margin-bottom: 0.65rem; }
        .metric-row {
            display: flex; justify-content: space-between; gap: 0.75rem; padding: 0.32rem 0;
            border-top: 1px solid #EEF2F7;
        }
        .metric-row:first-of-type { border-top: 0; }
        .metric-label { color: #64748B; font-size: 0.82rem; }
        .metric-value { color: #132033; font-size: 0.92rem; font-weight: 700; text-align: right; }
        .metric-diff.ok { color: #178A4C; }
        .metric-diff.bad { color: #C73737; }
        .metric-diff.incomplete { color: #A16207; }
        .section-title { color: #132033; font-size: 1.02rem; font-weight: 760; margin: 0.75rem 0 0.4rem 0; }
        .section-note { color: #64748B; font-size: 0.88rem; margin: -0.15rem 0 0.85rem 0; }
        .control-spacer { height: 1.78rem; }
        div[data-testid="stButton"] > button { color: #132033 !important; background: #FFFFFF !important; border: 1px solid #CBD5E1 !important; }
        div[data-testid="stButton"] > button p, div[data-testid="stButton"] > button span { color: #132033 !important; font-weight: 650 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# Generic Helpers
# =============================================================================
def get_config_value(*names, default=None):
    # Keboola apps can expose secrets either through st.secrets or env variables.
    for name in names:
        value = st.secrets.get(name) or os.environ.get(name)
        if value:
            return value
    return default


def normalize_column(value):
    # Normalize names so column detection works across variants like REV-IDL,
    # REV IDL, revenues_idl_ac_ytd, etc.
    return re.sub(r"[^A-Z0-9]+", "_", str(value).strip().upper()).strip("_")


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def parse_number(value):
    # Keboola/Snowflake exports may arrive as strings with spaces or comma decimals.
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace(" ", "").replace(",", ".")
    parsed = pd.to_numeric(value, errors="coerce")
    return 0.0 if pd.isna(parsed) else float(parsed)


def format_number(value):
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}".replace(",", " ")


def status_is_ok(value):
    return normalize_text(value) == "OK"


def diff_is_ok(value):
    if pd.isna(value):
        return False
    return abs(float(value)) <= OK_TOLERANCE


def period_sort_key(value):
    # Supports both 202601 and 2026-01 formats and keeps months sorted naturally.
    text = str(value).strip()
    match = re.match(r"^(\d{4})[-_ ]?(\d{2})$", text)
    if not match:
        return (9999, 99, text)
    return (int(match.group(1)), int(match.group(2)), text)


def is_2026_period(value):
    year, month, _ = period_sort_key(value)
    return year == 2026 and 1 <= month <= 12


# =============================================================================
# Column Discovery Helpers
# =============================================================================
def find_column(columns, include_terms, exclude_terms=None):
    # Generic helper used by build_metric. It lets us add new metrics by alias
    # instead of hardcoding exact physical column names.
    exclude_terms = exclude_terms or []
    for original, normalized in columns.items():
        if all(term in normalized for term in include_terms) and not any(term in normalized for term in exclude_terms):
            return original
    return None


def find_period_column(columns):
    preferred = ["CODE_PERIOD_VALUE", "PERIOD", "MONTH", "CODE_PERIOD"]
    for name in preferred:
        for original, normalized in columns.items():
            if normalized == name:
                return original
    for original, normalized in columns.items():
        if "PERIOD" in normalized or "MONTH" in normalized:
            return original
    return None


def find_group_company_column(columns):
    preferred = ["GROUP_COMPANY", "CODE_GROUP_COMPANY", "COMPANY", "GROUP_COMP"]
    for name in preferred:
        for original, normalized in columns.items():
            if normalized == name:
                return original
    for original, normalized in columns.items():
        if "GROUP" in normalized and "COMPANY" in normalized:
            return original
    return None


# =============================================================================
# UI Rendering Helpers
# =============================================================================
def render_status(ok_count, incomplete_count, total_count, selected_period):
    # Overall status priority: incomplete data first, then real OK/NOT OK.
    if incomplete_count:
        css_class = "fc-incomplete"
        title = "Incomplete data"
        note = f"{incomplete_count} of {total_count} checks have zero comparison values for period {selected_period}."
    elif ok_count == total_count:
        css_class = "fc-ok"
        title = "All controls OK"
        note = f"{ok_count} of {total_count} checks are OK for period {selected_period}."
    else:
        css_class = "fc-bad"
        title = "Controls need attention"
        note = f"{ok_count} of {total_count} checks are OK for period {selected_period}."

    st.markdown(
        f"""
        <div class="fc-status-band {css_class}">
            <div class="fc-status-title">{title}</div>
            <div class="fc-status-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_comparison_card(title, left_label, left_value, right_label, right_value, diff_value, state):
    status_text = {
        "ok": "OK",
        "bad": "NOT OK",
        "incomplete": "INCOMPLETE DATA",
    }[state]
    st.markdown(
        f"""
        <div class="metric-card {state}">
            <div class="metric-title">{title}</div>
            <div class="metric-row"><div class="metric-label">{left_label}</div><div class="metric-value">{format_number(left_value)}</div></div>
            <div class="metric-row"><div class="metric-label">{right_label}</div><div class="metric-value">{format_number(right_value)}</div></div>
            <div class="metric-row"><div class="metric-label">Difference</div><div class="metric-value metric-diff {state}">{format_number(diff_value)}</div></div>
            <div class="metric-row"><div class="metric-label">Status</div><div class="metric-value metric-diff {state}">{status_text}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title, idl_value, excel_value, diff_value, state):
    render_comparison_card(title, "IDL", idl_value, "Excel", excel_value, diff_value, state)


# =============================================================================
# Metric Definition Builders
# =============================================================================
def build_metric(columns, metric_name, aliases):
    # A metric is defined by detectable IDL, Excel, optional DIFF, and CHECK columns.
    # Example accepted names: PROFIT_IDL_AC_YTD, PROFIT_IDL_EXCEL_AC_YTD,
    # PROFIT_IDL_AC_YTD_CHECK.
    alias_terms = [normalize_column(alias) for alias in aliases]

    def metric_column(required_terms, excluded_terms=None):
        for alias in alias_terms:
            found = find_column(columns, [alias] + required_terms, excluded_terms)
            if found:
                return found
        return None

    return {
        "name": metric_name,
        "idl": metric_column(["IDL"], ["EXCEL", "CHECK", "STATUS", "DIFF"]),
        "excel": metric_column(["EXCEL"], ["CHECK", "STATUS", "DIFF"]),
        "diff": metric_column(["DIFF"]),
        "check": metric_column(["CHECK"]) or metric_column(["STATUS"]),
    }


def build_monthly_ytd_metric(columns, metric_name, aliases):
    # Monthly-vs-YTD checks live in a separate prepared table. The "monthly" side
    # is actually cumulative monthly data, e.g. REVENUES_IDL_AC_CALCULATED_YTD.
    # It is compared against the reported IDL YTD column for the same month.
    alias_terms = [normalize_column(alias) for alias in aliases]

    def metric_column(required_terms, excluded_terms=None):
        for alias in alias_terms:
            found = find_column(columns, [alias] + required_terms, excluded_terms)
            if found:
                return found
        return None

    calculated_ytd_column = metric_column(
        ["IDL", "CALCULATED", "YTD"],
        ["EXCEL", "CHECK", "STATUS", "DIFF"],
    )
    reported_ytd_column = metric_column(
        ["IDL", "YTD"],
        ["EXCEL", "CALCULATED", "CHECK", "STATUS", "DIFF"],
    )

    return {
        "name": metric_name,
        "monthly": calculated_ytd_column,
        "ytd": reported_ytd_column,
        "diff": metric_column(["DIFF"]),
        "check": metric_column(["CHECK"]) or metric_column(["STATUS"]),
    }


# =============================================================================
# Metric Value Calculators
# =============================================================================
def get_metric_values(period_slice, metric):
    # If either side is zero, the month is treated as not loaded yet instead of
    # failing the control. This avoids false red NOT OK states for open months.
    idl = period_slice[metric["idl"]].map(parse_number).sum()
    excel = period_slice[metric["excel"]].map(parse_number).sum()
    diff = period_slice[metric["diff"]].map(parse_number).sum() if metric["diff"] else idl - excel
    incomplete = abs(idl) <= OK_TOLERANCE or abs(excel) <= OK_TOLERANCE

    if incomplete:
        state = "incomplete"
    elif metric["check"]:
        state = "ok" if period_slice[metric["check"]].map(status_is_ok).all() else "bad"
    else:
        state = "ok" if diff_is_ok(diff) else "bad"

    return {"name": metric["name"], "idl": idl, "excel": excel, "diff": diff, "state": state}


def get_monthly_ytd_values(period_slice, metric):
    monthly = period_slice[metric["monthly"]].map(parse_number).sum()
    ytd = period_slice[metric["ytd"]].map(parse_number).sum()
    diff = period_slice[metric["diff"]].map(parse_number).sum() if metric["diff"] else monthly - ytd
    incomplete = abs(monthly) <= OK_TOLERANCE or abs(ytd) <= OK_TOLERANCE

    if incomplete:
        state = "incomplete"
    elif metric["check"]:
        state = "ok" if period_slice[metric["check"]].map(status_is_ok).all() else "bad"
    else:
        state = "ok" if diff_is_ok(diff) else "bad"

    return {"name": metric["name"], "monthly": monthly, "ytd": ytd, "diff": diff, "state": state}


# =============================================================================
# Schema Validation Helpers
# =============================================================================
def show_schema_help(df, metrics):
    # Fail with a useful schema diagnostic if the prepared table changes shape.
    missing = []
    for metric in metrics:
        for key in ["idl", "excel"]:
            if not metric[key]:
                missing.append(f"{metric['name']} {key.upper()}")
        if not metric["check"] and not metric["diff"]:
            missing.append(f"{metric['name']} CHECK or DIFF")
    if missing:
        st.error("Could not identify required control columns: " + ", ".join(missing))
        st.caption(
            "Expected names like REVENUES_IDL_AC_YTD, REVENUES_IDL_EXCEL_AC_YTD, REVENUES_IDL_AC_YTD_CHECK, "
            "EBITDA_IDL_AC_YTD, EBITDA_IDL_EXCEL_AC_YTD, EBITDA_IDL_AC_YTD_CHECK, "
            "CONSO_ADJUSTMENTS_IDL_AC_YTD, CONSO_ADJUSTMENTS_IDL_EXCEL_AC_YTD, CONSO_ADJUSTMENTS_IDL_AC_YTD_CHECK, "
            "PROFIT_IDL_AC_YTD, PROFIT_IDL_EXCEL_AC_YTD, PROFIT_IDL_AC_YTD_CHECK."
        )
        st.dataframe(pd.DataFrame({"Available columns": df.columns.tolist()}), use_container_width=True)
        st.stop()


def show_monthly_ytd_schema_help(df, metrics):
    missing = []
    for metric in metrics:
        for key in ["monthly", "ytd"]:
            if not metric[key]:
                missing.append(f"{metric['name']} {key.upper()}")
        if not metric["check"] and not metric["diff"]:
            missing.append(f"{metric['name']} CHECK or DIFF")
    if missing:
        st.error("Could not identify required monthly-vs-YTD columns: " + ", ".join(missing))
        st.caption(
            "Expected names like REVENUES_IDL_AC_CALCULATED_YTD and REVENUES_IDL_AC_YTD "
            "plus optional CHECK/DIFF columns for Revenue, EBITDA, and Profit."
        )
        st.dataframe(pd.DataFrame({"Available columns": df.columns.tolist()}), use_container_width=True)
        st.stop()


def build_balance_sheet_controls(df, period_column, group_company_column):
    # Balance sheet rows are already scoped to CBS2 in the prepared Keboola table.
    # A company is OK when the YTD balance amount is exactly zero within tolerance.
    period_df = df[df[period_column] == selected_period].copy()
    if period_df.empty:
        st.warning(f"No balance sheet rows found for period {selected_period}.")
        st.stop()

    period_df["BALANCE_AMOUNT_YTD"] = period_df["BALANCE_AMOUNT_YTD"].map(parse_number)
    result_df = (
        period_df.groupby(group_company_column, dropna=False)["BALANCE_AMOUNT_YTD"]
        .sum()
        .reset_index()
        .rename(columns={group_company_column: "Group company", "BALANCE_AMOUNT_YTD": "Balance amount YTD"})
        .sort_values("Group company")
    )
    result_df["Status"] = result_df["Balance amount YTD"].map(
        lambda value: "OK" if diff_is_ok(value) else "NOT OK"
    )
    return result_df


# =============================================================================
# Keboola Client and Data Loaders
# =============================================================================
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
    # Cached for 10 minutes; the Refresh button below clears this cache manually.
    return keboola.read_table(TABLE_ID)


@st.cache_data(ttl=600)
def load_monthly_ytd_controls():
    return keboola.read_table(MONTHLY_YTD_TABLE_ID)


@st.cache_data(ttl=600)
def load_balance_sheet_controls():
    return keboola.read_table(BALANCE_SHEET_TABLE_ID)


# =============================================================================
# Load Source Tables
# =============================================================================
# Load and validate the prepared controls table before rendering the dashboard.
with st.spinner("Loading 2026 control dashboard data from Keboola..."):
    try:
        controls_df = load_controls()
    except Exception as exc:
        st.error(f"Could not load table {TABLE_ID}: {exc}")
        st.stop()

if controls_df.empty:
    st.warning(f"Table {TABLE_ID} is empty.")
    st.stop()

with st.spinner("Loading monthly vs YTD control data from Keboola..."):
    try:
        monthly_ytd_df = load_monthly_ytd_controls()
    except Exception as exc:
        st.error(f"Could not load table {MONTHLY_YTD_TABLE_ID}: {exc}")
        st.stop()

if monthly_ytd_df.empty:
    st.warning(f"Table {MONTHLY_YTD_TABLE_ID} is empty.")
    st.stop()

with st.spinner("Loading balance sheet control data from Keboola..."):
    try:
        balance_sheet_df = load_balance_sheet_controls()
    except Exception as exc:
        st.error(f"Could not load table {BALANCE_SHEET_TABLE_ID}: {exc}")
        st.stop()

if balance_sheet_df.empty:
    st.warning(f"Table {BALANCE_SHEET_TABLE_ID} is empty.")
    st.stop()


# =============================================================================
# Prepare IDL vs Excel Controls
# =============================================================================
controls_df = controls_df.copy()
columns = {column: normalize_column(column) for column in controls_df.columns}
period_column = find_period_column(columns)
if not period_column:
    st.error("Could not identify period column in ADS_CONTROLS_2026.")
    st.dataframe(pd.DataFrame({"Available columns": controls_df.columns.tolist()}), use_container_width=True)
    st.stop()

controls_df[period_column] = controls_df[period_column].fillna("").astype(str).str.strip()
period_options = sorted(
    [period for period in controls_df[period_column].unique().tolist() if is_2026_period(period)],
    key=period_sort_key,
)
if not period_options:
    st.warning("No 2026 periods found in ADS_CONTROLS_2026.")
    st.dataframe(controls_df.sort_values(period_column).head(30), use_container_width=True)
    st.stop()

metrics = [
    # Display order of cards and status columns.
    build_metric(columns, "Revenue", ["REV", "REVENUE", "REVENUES"]),
    build_metric(columns, "EBITDA", ["EBITDA"]),
    build_metric(columns, "Profit", ["PROFIT", "PROFITS", "NET_PROFIT", "PBT", "EARNINGS"]),
    build_metric(columns, "Conso Adjustments", ["CONSO", "CONSOLIDATION", "ADJ", "ADJUSTMENT", "ADJUSTMENTS"]),
]
show_schema_help(controls_df, metrics)


# =============================================================================
# Prepare Calculated Monthly YTD vs Reported YTD Controls
# =============================================================================
monthly_ytd_df = monthly_ytd_df.copy()
monthly_ytd_columns = {column: normalize_column(column) for column in monthly_ytd_df.columns}
monthly_ytd_period_column = find_period_column(monthly_ytd_columns)
if not monthly_ytd_period_column:
    st.error("Could not identify period column in ADS_CONTROLS_M_YTD_2026.")
    st.dataframe(pd.DataFrame({"Available columns": monthly_ytd_df.columns.tolist()}), use_container_width=True)
    st.stop()

monthly_ytd_df[monthly_ytd_period_column] = monthly_ytd_df[monthly_ytd_period_column].fillna("").astype(str).str.strip()
monthly_ytd_metrics = [
    build_monthly_ytd_metric(monthly_ytd_columns, "Revenue", ["REV", "REVENUE", "REVENUES"]),
    build_monthly_ytd_metric(monthly_ytd_columns, "EBITDA", ["EBITDA"]),
    build_monthly_ytd_metric(monthly_ytd_columns, "Profit", ["PROFIT", "PROFITS", "NET_PROFIT", "PBT", "EARNINGS"]),
]
show_monthly_ytd_schema_help(monthly_ytd_df, monthly_ytd_metrics)


# =============================================================================
# Prepare Balance Sheet Controls
# =============================================================================
balance_sheet_df = balance_sheet_df.copy()
balance_sheet_columns = {column: normalize_column(column) for column in balance_sheet_df.columns}
balance_sheet_period_column = find_period_column(balance_sheet_columns)
balance_sheet_group_company_column = find_group_company_column(balance_sheet_columns)
if not balance_sheet_period_column:
    st.error("Could not identify period column in ADS_CONTROLS_BS_2026.")
    st.dataframe(pd.DataFrame({"Available columns": balance_sheet_df.columns.tolist()}), use_container_width=True)
    st.stop()
if not balance_sheet_group_company_column:
    st.error("Could not identify group company column in ADS_CONTROLS_BS_2026.")
    st.dataframe(pd.DataFrame({"Available columns": balance_sheet_df.columns.tolist()}), use_container_width=True)
    st.stop()
if "BALANCE_AMOUNT_YTD" not in balance_sheet_df.columns:
    st.error("Could not identify BALANCE_AMOUNT_YTD column in ADS_CONTROLS_BS_2026.")
    st.dataframe(pd.DataFrame({"Available columns": balance_sheet_df.columns.tolist()}), use_container_width=True)
    st.stop()

balance_sheet_df[balance_sheet_period_column] = (
    balance_sheet_df[balance_sheet_period_column].fillna("").astype(str).str.strip()
)

default_period = period_options[-1]


# =============================================================================
# Dashboard Header and Global Controls
# =============================================================================
st.markdown(
    """
    <div class="fc-hero">
        <div class="fc-title">Financial Checks</div>
        <div class="fc-subtitle">2026 control dashboard based on prepared ADS_CONTROLS_2026 results.</div>
        <div class="fc-pill-row">
            <span class="fc-pill">Revenue: IDL vs Excel</span>
            <span class="fc-pill">EBITDA: IDL vs Excel</span>
            <span class="fc-pill">Profit: IDL vs Excel</span>
            <span class="fc-pill">Conso adjustments: IDL vs Excel</span>
            <span class="fc-pill">Status from CHECK columns</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

filter_col, pbi_col, refresh_col = st.columns([2.2, 1.25, 1])
with filter_col:
    selected_period = st.selectbox("Period", period_options, index=period_options.index(default_period))
with pbi_col:
    st.markdown('<div class="control-spacer"></div>', unsafe_allow_html=True)
    st.link_button("Open Power BI detail", POWER_BI_DETAIL_URL, use_container_width=True)
    st.caption("Opens the Power BI report with control details.")
with refresh_col:
    st.markdown('<div class="control-spacer"></div>', unsafe_allow_html=True)
    if st.button("Refresh data", use_container_width=True):
        # Useful after Keboola refreshes ADS_CONTROLS_2026 and Streamlit still
        # has the old table cached.
        st.cache_data.clear()
        st.rerun()
    st.caption("Reloads the Keboola table cache.")

period_df = controls_df[controls_df[period_column] == selected_period]
if period_df.empty:
    st.warning(f"No rows found for period {selected_period}.")
    st.stop()


# =============================================================================
# Section 1: IDL vs Excel Controls
# =============================================================================
metric_values = [get_metric_values(period_df, metric) for metric in metrics]
ok_count = sum(metric["state"] == "ok" for metric in metric_values)
incomplete_count = sum(metric["state"] == "incomplete" for metric in metric_values)

with st.container(border=True):
    st.markdown('<div class="section-title">IDL vs Excel Controls</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Compares prepared IDL figures against Excel control values from ADS_CONTROLS_2026. <strong>Revenue, EBITDA and Profit are CBS2 figures</strong>; Conso Adjustments represent consolidation adjustments.</div>',
        unsafe_allow_html=True,
    )
    render_status(ok_count, incomplete_count, len(metric_values), selected_period)

    # Main KPI cards for the selected month.
    metric_cols = st.columns(len(metric_values))
    for col, metric in zip(metric_cols, metric_values):
        with col:
            render_metric_card(metric["name"], metric["idl"], metric["excel"], metric["diff"], metric["state"])

monthly_ytd_period_df = monthly_ytd_df[monthly_ytd_df[monthly_ytd_period_column] == selected_period]
if monthly_ytd_period_df.empty:
    st.warning(f"No monthly vs YTD rows found for period {selected_period}.")
    st.stop()


# =============================================================================
# Section 2: Calculated Monthly YTD vs Reported YTD
# =============================================================================
monthly_ytd_values = [
    get_monthly_ytd_values(monthly_ytd_period_df, metric) for metric in monthly_ytd_metrics
]
monthly_ytd_ok_count = sum(metric["state"] == "ok" for metric in monthly_ytd_values)
monthly_ytd_incomplete_count = sum(metric["state"] == "incomplete" for metric in monthly_ytd_values)

with st.container(border=True):
    st.markdown('<div class="section-title">Calculated Monthly YTD vs Reported YTD</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Compares cumulatively calculated monthly values, e.g. REVENUES_IDL_AC_CALCULATED_YTD, against reported IDL YTD values from ADS_CONTROLS_M_YTD_2026.</div>',
        unsafe_allow_html=True,
    )
    render_status(
        monthly_ytd_ok_count,
        monthly_ytd_incomplete_count,
        len(monthly_ytd_values),
        selected_period,
    )

    monthly_ytd_cols = st.columns(len(monthly_ytd_values))
    for col, metric in zip(monthly_ytd_cols, monthly_ytd_values):
        with col:
            render_comparison_card(
                metric["name"],
                "Calculated monthly YTD",
                metric["monthly"],
                "Reported YTD",
                metric["ytd"],
                metric["diff"],
                metric["state"],
            )


# =============================================================================
# Section 3: Balance Sheet by Group Company
# =============================================================================
balance_sheet_result_df = build_balance_sheet_controls(
    balance_sheet_df,
    balance_sheet_period_column,
    balance_sheet_group_company_column,
)
balance_sheet_ok_count = (balance_sheet_result_df["Status"] == "OK").sum()

with st.container(border=True):
    st.markdown('<div class="section-title">Balance Sheet by Group Company</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Checks CBS2 balance sheet totals by group company from ADS_CONTROLS_BS_2026. BALANCE_AMOUNT_YTD must be zero to pass.</div>',
        unsafe_allow_html=True,
    )
    render_status(balance_sheet_ok_count, 0, len(balance_sheet_result_df), selected_period)
    st.dataframe(
        balance_sheet_result_df.style.format({"Balance amount YTD": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
        height=280,
    )


# =============================================================================
# Trend and Period Overview
# =============================================================================
trend_rows = []
# Build one row per month for trend lines and the status overview table.
for period in period_options:
    period_slice = controls_df[controls_df[period_column] == period]
    row = {"Period": period}
    for metric in metrics:
        values = get_metric_values(period_slice, metric)
        row[f"{metric['name']} Diff"] = values["diff"]
        row[f"{metric['name']} Status"] = {"ok": "OK", "bad": "NOT OK", "incomplete": "INCOMPLETE DATA"}[values["state"]]
    trend_rows.append(row)

trend_df = pd.DataFrame(trend_rows).set_index("Period")

st.divider()
st.markdown('<div class="section-title">2026 Status Overview</div>', unsafe_allow_html=True)
status_table = trend_df.reset_index()
diff_format = {column: "{:,.0f}" for column in status_table.columns if column.endswith(" Diff")}
st.dataframe(
    status_table.style.format(diff_format),
    use_container_width=True,
    hide_index=True,
    height=360,
)


# =============================================================================
# Debug / Diagnostics
# =============================================================================
with st.expander("Source data and detected columns"):
    # Developer/debug view: shows how aliases mapped to real Keboola columns.
    detected = []
    for metric in metrics:
        detected.append(
            {
                "Metric": metric["name"],
                "IDL column": metric["idl"],
                "Excel column": metric["excel"],
                "Diff column": metric["diff"] or "calculated from IDL - Excel",
                "Check column": metric["check"],
            }
        )
    st.dataframe(pd.DataFrame(detected), use_container_width=True, hide_index=True)
    monthly_ytd_detected = []
    for metric in monthly_ytd_metrics:
        monthly_ytd_detected.append(
            {
                "Metric": metric["name"],
                "Monthly column": metric["monthly"],
                "YTD column": metric["ytd"],
                "Diff column": metric["diff"] or "calculated from Monthly - YTD",
                "Check column": metric["check"],
            }
        )
    st.dataframe(pd.DataFrame(monthly_ytd_detected), use_container_width=True, hide_index=True)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Period column": balance_sheet_period_column,
                    "Group company column": balance_sheet_group_company_column,
                    "Amount column": "BALANCE_AMOUNT_YTD",
                    "Source table": BALANCE_SHEET_TABLE_ID,
                }
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        controls_df.sort_values(period_column, key=lambda series: series.map(period_sort_key)),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        monthly_ytd_df.sort_values(monthly_ytd_period_column, key=lambda series: series.map(period_sort_key)),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        balance_sheet_df.sort_values(balance_sheet_period_column, key=lambda series: series.map(period_sort_key)),
        use_container_width=True,
        hide_index=True,
    )
