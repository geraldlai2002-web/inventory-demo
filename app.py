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
    df = pd.read_csv(file_obj) if file_obj.name.endswith('.csv') else pd.read_excel(file_obj)
    # Set the first column as index, but ensure it's treated as strings
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    return df.set_index(df.columns[0])

if file_old and file_new:
    df_old = load_and_parse(file_old)
    df_new = load_and_parse(file_new)
    
    # 1. Filter both DataFrames to keep ONLY numeric columns
    df_old_num = df_old.select_dtypes(include=['number'])
    df_new_num = df_new.select_dtypes(include=['number'])
    
    # 2. Align by common IDs
    common_ids = df_old_num.index.intersection(df_new_num.index)
    df_old_num = df_old_num.loc[common_ids]
    df_new_num = df_new_num.loc[common_ids]
    
    # 3. Now the subtraction will work safely
    diff = df_new_num - df_old_num
    
    # Filter only cells with significant variance
    mask = diff.abs() > 0.01
    changed_items = diff[mask].stack().reset_index()
    changed_items.columns = ['Stock ID', 'Metric', 'Variance']
    
    if not changed_items.empty:
        st.error(f"Found {len(changed_items)} discrepancies:")
        st.dataframe(changed_items, use_container_width=True)
    else:
        st.success("Files match perfectly.")
