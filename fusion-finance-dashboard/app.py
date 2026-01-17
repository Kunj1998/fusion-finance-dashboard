import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ======================= PAGE CONFIG =======================
st.set_page_config(page_title="Fusion Finance Dashboard", layout="wide")

# ======================= CUSTOM CSS =======================
st.markdown(
    """
    <style>
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 20px;
        margin-bottom: 25px;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1e1e2f, #2a2a40);
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(0,255,255,0.15);
        text-align: center;
        color: white;
        min-height: 115px;
    }
    .kpi-title {
        font-size: 14px;
        color: #9aa4b2;
    }
    .kpi-value {
        font-size: 30px;
        font-weight: 700;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================= FILE PATH =======================
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "Fusion_1_30_Allocation.xlsb")

# ======================= LOAD DATA =======================
@st.cache_data
def load_data(path):
    df = pd.read_excel(path, engine="pyxlsb")
    df.columns = [str(c).strip() for c in df.columns]

    numeric_cols = [
        "No of Loans",
        "Dailed Customers",
        "Connect",
        "Nos. of PTP",
        "Nos of Loans Paid",
        "Intensity",
        "Collection Amount",
        "Principal Outstanding",
        "POS 100%",
        "Total Amt 100%",
        "Total Default Amount"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

# ======================= LOAD EXCEL =======================
if not os.path.exists(DATA_PATH):
    st.error("Excel file not found. Check file name & location.")
    st.stop()

df = load_data(DATA_PATH)

# ======================= AUTO COLUMN DETECT =======================
def find_col(keys):
    for c in df.columns:
        for k in keys:
            if k in c.lower():
                return c
    return None

state_col = find_col(["state"])
dpd_col = find_col(["dpd"])

if not state_col or not dpd_col:
    st.error("State / DPD column not found in Excel")
    st.stop()

# ======================= SIDEBAR FILTERS =======================
st.sidebar.header("Filters")

state = st.sidebar.selectbox(
    "Select State",
    ["All"] + sorted(df[state_col].astype(str).unique())
)

dpd = st.sidebar.selectbox(
    "Select DPD Bucket",
    ["All"] + sorted(df[dpd_col].astype(str).unique())
)

connect_filter = st.sidebar.selectbox(
    "Connect Status",
    ["All", "Connected", "Not Connected"]
)

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ======================= APPLY FILTERS =======================
filtered_df = df.copy()

if state != "All":
    filtered_df = filtered_df[filtered_df[state_col].astype(str) == state]

if dpd != "All":
    filtered_df = filtered_df[filtered_df[dpd_col].astype(str) == dpd]

if connect_filter == "Connected":
    filtered_df = filtered_df[filtered_df["Connect"] > 0]
elif connect_filter == "Not Connected":
    filtered_df = filtered_df[filtered_df["Connect"] == 0]

# ======================= HELPERS =======================
def total(col):
    return int(filtered_df[col].sum()) if col in filtered_df.columns else 0

def crore(col):
    return round(filtered_df[col].sum() / 1e7, 2) if col in filtered_df.columns else 0

# ======================= HEADER =======================
st.markdown("## Fusion Finance Recovery Dashboard")
st.caption("State | DPD | Connect Based MIS Dashboard")

# ======================= KPI SECTION =======================
st.markdown(
    f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-title">No of Loans</div><div class="kpi-value">{total('No of Loans')}</div></div>
      <div class="kpi-card"><div class="kpi-title">Dialed</div><div class="kpi-value">{total('Dailed Customers')}</div></div>
      <div class="kpi-card"><div class="kpi-title">Connected</div><div class="kpi-value">{total('Connect')}</div></div>
      <div class="kpi-card"><div class="kpi-title">PTP</div><div class="kpi-value">{total('Nos. of PTP')}</div></div>
      <div class="kpi-card"><div class="kpi-title">Intensity</div><div class="kpi-value">{total('Intensity')}</div></div>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-title">Collection (Cr)</div><div class="kpi-value">{crore('Collection Amount')}</div></div>
      <div class="kpi-card"><div class="kpi-title">POS (Cr)</div><div class="kpi-value">{crore('Principal Outstanding')}</div></div>
      <div class="kpi-card"><div class="kpi-title">Default (Cr)</div><div class="kpi-value">{crore('Total Default Amount')}</div></div>
    </div>
    """,
    unsafe_allow_html=True
)

# ======================= GRAPHS =======================
st.divider()
st.markdown("Performance Insights")

state_summary = filtered_df.groupby(state_col)[
    ["Collection Amount", "Principal Outstanding"]
].sum().reset_index()

state_summary["Collection Cr"] = state_summary["Collection Amount"] / 1e7
state_summary["POS Cr"] = state_summary["Principal Outstanding"] / 1e7

st.plotly_chart(
    px.bar(
        state_summary,
        x=state_col,
        y=["Collection Cr", "POS Cr"],
        barmode="group",
        title="State-wise Collection vs POS"
    ),
    use_container_width=True
)

dpd_summary = filtered_df.groupby(dpd_col)["Collection Amount"].sum().reset_index()
dpd_summary["Collection Cr"] = dpd_summary["Collection Amount"] / 1e7

st.plotly_chart(
    px.bar(
        dpd_summary,
        x=dpd_col,
        y="Collection Cr",
        title="DPD Bucket-wise Collection",
        color="Collection Cr",
        color_continuous_scale="turbo"
    ),
    use_container_width=True
)

# ======================= TABLE =======================
st.divider()
st.markdown("Filtered Data")
st.dataframe(filtered_df, height=420)
st.success(f"Total Records: {len(filtered_df)}")


