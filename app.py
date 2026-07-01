import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventory Delta Tracker", layout="wide")
st.title("⚖️ Inventory Delta Tracker")

col1, col2 = st.columns(2)
file_old = col1.file_uploader("Upload Baseline File", type=["csv"])
file_new = col2.file_uploader("Upload New Master File", type=["csv"])

def clean_data(file_obj):
    # 1. Read the file, skipping the first 6 rows of metadata
    df = pd.read_csv(file_obj, skiprows=6)
    
    # 2. Keep only rows where 'Stk Code' is a valid code (starts with 'D')
    # This automatically ignores 'Grand Total', 'PMAT', and empty lines
    df = df[df['Stk Code'].str.startswith('D', na=False)].copy()
    
    # 3. Force columns to numeric
    metrics = ['Prev. Qty', 'In Qty', 'Transfer', 'Transform', 'Issue Qty', 'Del. Qty', 'Bal Qty']
    for m in metrics:
        df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0)
        
    return df.set_index('Stk Code')[metrics]

if file_old and file_new:
    df1 = clean_data(file_old)
    df2 = clean_data(file_new)
    
    # Calculate difference
    diff = df2 - df1
    
    # Show only rows where the sum of absolute differences is not zero
    changed = diff[(diff.abs().sum(axis=1) > 0)]
    
    if not changed.empty:
        st.error("Differences detected:")
        st.dataframe(changed, use_container_width=True)
    else:
        st.success("Files are identical!")
