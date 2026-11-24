import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Global Superstore Analysis", page_icon="📊", layout="wide")

st.title("📊 Global Superstore Analysis")
st.caption("Interactive dashboard • 3 visualizations • 2 analysis stories")

@st.cache_data(show_spinner=False)
def load_file(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            file.seek(0)
            return pd.read_csv(file, encoding="latin1")
    if name.endswith(".xls") or name.endswith(".xlsx"):
        return pd.read_excel(file)
    raise ValueError("File harus CSV, XLS, atau XLSX.")

uploaded = st.file_uploader("Upload dataset Global Superstore (CSV, XLS, atau XLSX)", type=["csv", "xls", "xlsx"])

if uploaded is None:
    st.info("Upload file Global Superstore untuk mulai melihat dashboard. File dataset tidak tersimpan di aplikasi ini.")
    st.stop()

try:
    df = load_file(uploaded)
except Exception as e:
    st.error(f"File tidak berhasil dibaca: {e}")
    st.stop()

# Normalize column names while preserving original names
col_map = {str(c).strip().lower(): c for c in df.columns}
def find_col(*names):
    for name in names:
        if name.lower() in col_map:
            return col_map[name.lower()]
    return None

sales_col = find_col("Sales", "Sale")
profit_col = find_col("Profit")
category_col = find_col("Category")
region_col = find_col("Region")
date_col = find_col("Order Date", "OrderDate", "Date")
subcat_col = find_col("Sub-Category", "Sub Category", "Subcategory")
segment_col = find_col("Segment")

if sales_col is None:
    st.error("Kolom Sales tidak ditemukan. Pastikan dataset memiliki kolom 'Sales'.")
    st.write("Kolom yang terbaca:", list(df.columns))
    st.stop()

# Convert numeric and date fields
for c in [sales_col, profit_col]:
    if c is not None:
        df[c] = pd.to_numeric(df[c], errors="coerce")
if date_col is not None:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# Sidebar filters
st.sidebar.header("Filter Data")
filtered = df.copy()
if region_col is not None:
    vals = sorted(filtered[region_col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect("Region", vals, default=vals)
    filtered = filtered[filtered[region_col].astype(str).isin(chosen)]
if category_col is not None:
    vals = sorted(filtered[category_col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect("Category", vals, default=vals)
    filtered = filtered[filtered[category_col].astype(str).isin(chosen)]
if date_col is not None and filtered[date_col].notna().any():
    min_date = filtered[date_col].min().date()
    max_date = filtered[date_col].max().date()
    date_range = st.sidebar.date_input("Order Date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered[date_col].dt.date >= start) & (filtered[date_col].dt.date <= end)]

# Navigation
page = st.sidebar.radio("Halaman", ["Dashboard", "Worksheet 1 - Sales by Category", "Worksheet 2 - Profit by Region", "Worksheet 3 - Monthly Sales Trend", "Story 1 - Sales Performance", "Story 2 - Profitability"])

sales_total = filtered[sales_col].sum()
profit_total = filtered[profit_col].sum() if profit_col is not None else None
rows_total = len(filtered)

if page == "Dashboard":
    st.header("Global Superstore Sales Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sales", f"{sales_total:,.2f}")
    m2.metric("Total Profit", f"{profit_total:,.2f}" if profit_total is not None else "Kolom Profit tidak ada")
    m3.metric("Total Records", f"{rows_total:,}")
    left, right = st.columns(2)
    with left:
        if category_col is not None:
            cat = filtered.groupby(category_col, dropna=False)[sales_col].sum().reset_index().sort_values(sales_col, ascending=False)
            fig = px.bar(cat, x=category_col, y=sales_col, title="Sales by Category", labels={sales_col: "Sales", category_col: "Category"}, text_auto=".2s")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Kolom Category tidak ditemukan.")
    with right:
        if region_col is not None and profit_col is not None:
            reg = filtered.groupby(region_col, dropna=False)[profit_col].sum().reset_index().sort_values(profit_col, ascending=False)
            fig = px.bar(reg, x=region_col, y=profit_col, title="Profit by Region", color=profit_col, labels={profit_col: "Profit", region_col: "Region"}, text_auto=".2s")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Kolom Region atau Profit tidak ditemukan.")
    if date_col is not None:
        monthly = filtered.dropna(subset=[date_col]).copy()
        monthly["Month"] = monthly[date_col].dt.to_period("M").dt.to_timestamp()
        monthly = monthly.groupby("Month")[sales_col].sum().reset_index()
        fig = px.line(monthly, x="Month", y=sales_col, title="Monthly Sales Trend", markers=True, labels={sales_col: "Sales"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Kolom Order Date tidak ditemukan.")

elif page == "Worksheet 1 - Sales by Category":
    st.header("Worksheet 1: Sales by Category")
    if category_col is not None:
        cat = filtered.groupby(category_col, dropna=False)[sales_col].sum().reset_index().sort_values(sales_col, ascending=False)
        fig = px.bar(cat, x=category_col, y=sales_col, title="Total Sales by Category", text_auto=".2s", labels={sales_col: "Sales"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(cat, use_container_width=True)
    else:
        st.error("Kolom Category tidak ditemukan.")

elif page == "Worksheet 2 - Profit by Region":
    st.header("Worksheet 2: Profit by Region")
    if region_col is not None and profit_col is not None:
        reg = filtered.groupby(region_col, dropna=False)[profit_col].sum().reset_index().sort_values(profit_col, ascending=False)
        fig = px.bar(reg, x=region_col, y=profit_col, title="Total Profit by Region", color=profit_col, text_auto=".2s", labels={profit_col: "Profit"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(reg, use_container_width=True)
    else:
        st.error("Kolom Region atau Profit tidak ditemukan.")

elif page == "Worksheet 3 - Monthly Sales Trend":
    st.header("Worksheet 3: Monthly Sales Trend")
    if date_col is not None:
        monthly = filtered.dropna(subset=[date_col]).copy()
        monthly["Month"] = monthly[date_col].dt.to_period("M").dt.to_timestamp()
        monthly = monthly.groupby("Month")[sales_col].sum().reset_index()
        fig = px.line(monthly, x="Month", y=sales_col, title="Sales per Month", markers=True, labels={sales_col: "Sales"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(monthly, use_container_width=True)
    else:
        st.error("Kolom tanggal Order Date tidak ditemukan.")

elif page == "Story 1 - Sales Performance":
    st.header("Story 1: Sales Performance Analysis")
    st.markdown("### 1. Sales by Category")
    if category_col is not None:
        cat = filtered.groupby(category_col, dropna=False)[sales_col].sum().reset_index().sort_values(sales_col, ascending=False)
        st.plotly_chart(px.bar(cat, x=category_col, y=sales_col, title="Sales by Category", text_auto=".2s"), use_container_width=True)
    st.markdown("### 2. Monthly Sales Trend")
    if date_col is not None:
        monthly = filtered.dropna(subset=[date_col]).copy()
        monthly["Month"] = monthly[date_col].dt.to_period("M").dt.to_timestamp()
        monthly = monthly.groupby("Month")[sales_col].sum().reset_index()
        st.plotly_chart(px.line(monthly, x="Month", y=sales_col, title="Monthly Sales Trend", markers=True), use_container_width=True)
    st.markdown("### Ringkasan")
    st.write(f"Total penjualan pada data yang terfilter adalah **{sales_total:,.2f}**.")

else:
    st.header("Story 2: Profitability Analysis")
    if region_col is not None and profit_col is not None:
        reg = filtered.groupby(region_col, dropna=False)[profit_col].sum().reset_index().sort_values(profit_col, ascending=False)
        st.plotly_chart(px.bar(reg, x=region_col, y=profit_col, title="Profit by Region", color=profit_col, text_auto=".2s"), use_container_width=True)
        if not reg.empty:
            best = reg.iloc[0]
            worst = reg.iloc[-1]
            st.write(f"Region dengan profit tertinggi: **{best[region_col]}** ({best[profit_col]:,.2f}).")
            st.write(f"Region dengan profit terendah: **{worst[region_col]}** ({worst[profit_col]:,.2f}).")
    else:
        st.warning("Kolom Region atau Profit tidak ditemukan.")
    st.markdown("### Ringkasan")
    st.write(f"Total profit pada data yang terfilter adalah **{profit_total:,.2f}**." if profit_total is not None else "Kolom Profit tidak tersedia.")

with st.expander("Lihat data yang digunakan"):
    st.dataframe(filtered, use_container_width=True)
