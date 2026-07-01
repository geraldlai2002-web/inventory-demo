import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventory Delta Tracker", layout="wide")
st.title("⚖️ Inventory Delta Tracker")

col1, col2 = st.columns(2)
file_old = col1.file_uploader("Upload Baseline File", type=["csv"])
file_new = col2.file_uploader("Upload New Master File", type=["csv"])

def clean_and_load(file_obj):
    # 1. Read the raw CSV as a list of lines to find the header
    lines = file_obj.readlines()
    header_line = 0
    for i, line in enumerate(lines):
        if b"Stk Code" in line:
            header_line = i
            break
    
    # 2. Reset the file pointer and load using the discovered header row
    file_obj.seek(0)
    df = pd.read_csv(file_obj, skiprows=header_line)
    
    # 3. Keep only rows that start with 'D' (The actual Stock IDs)
    # This automatically discards 'PMAT', 'Grand Total', and header debris
    df = df[df['Stk Code'].astype(str).str.startswith('D')].copy()
    
    # 4. Convert numeric columns, treating empty/errors as 0
    metrics = ['Prev. Qty', 'In Qty', 'Transfer', 'Transform', 'Issue Qty', 'Del. Qty', 'Bal Qty']
    for m in metrics:
        df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0)
        
    return df.set_index('Stk Code')[metrics]

if file_old and file_new:
    df1 = clean_and_load(file_old)
    df2 = clean_and_load(file_new)
    
    # Compare
    diff = df2 - df1
    # Filter for rows where any change happened
    changed = diff[(diff != 0).any(axis=1)]
    
    if not changed.empty:
        st.error(f"⚠️ Differences found in {len(changed)} items:")
        st.dataframe(changed, use_container_width=True)
    else:
        st.success("✅ Files match perfectly.")
