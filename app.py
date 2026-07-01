import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Quick Inventory Comparator", layout="wide")
st.title("⚖️ Quick Inventory Comparator")

col1, col2 = st.columns(2)
with col1:
    file_old = st.file_uploader("Upload Baseline File", type=["xlsx", "csv"])
with col2:
    file_new = st.file_uploader("Upload New File", type=["xlsx", "csv"])

def load_and_parse(file_obj):
    # Reads file and returns a DataFrame indexed by the first column (Stock ID)
    df = pd.read_csv(file_obj) if file_obj.name.endswith('.csv') else pd.read_excel(file_obj)
    # Assume first column is 'Stock ID'
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    return df.set_index(df.columns[0])

if file_old and file_new:
    df_old = load_and_parse(file_old)
    df_new = load_and_parse(file_new)
    
    # Align both files by common Stock IDs
    common_ids = df_old.index.intersection(df_new.index)
    df_old = df_old.loc[common_ids]
    df_new = df_new.loc[common_ids]
    
    # Calculate difference
    diff = df_new - df_old
    
    # Filter only cells with significant variance
    mask = diff.abs() > 0.01
    changed_items = diff[mask].stack().reset_index()
    changed_items.columns = ['Stock ID', 'Metric', 'Variance']
    
    if not changed_items.empty:
        st.error(f"Found {len(changed_items)} discrepancies:")
        st.dataframe(changed_items, use_container_width=True)
    else:
        st.success("Files match perfectly.")
