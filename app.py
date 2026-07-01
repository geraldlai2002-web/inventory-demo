import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventory Delta Tracker", layout="wide")
st.title("⚖️ Inventory Delta Tracker")

col1, col2 = st.columns(2)
file_old = col1.file_uploader("Upload Baseline (2025_mini)", type=["csv", "xlsx"])
file_new = col2.file_uploader("Upload New Master", type=["csv", "xlsx"])

def process_file(file_obj):
    # 1. Read file, find the row with 'Stk Code' as the header
    df = pd.read_csv(file_obj) if file_obj.name.endswith('.csv') else pd.read_excel(file_obj)
    
    # Locate where the actual data starts (where 'Stk Code' exists)
    # The snippet shows headers are on row 6 (index 5)
    header_idx = df[df.iloc[:, 0] == 'Stk Code'].index[0]
    df = pd.read_csv(file_obj, skiprows=header_idx) if file_obj.name.endswith('.csv') \
         else pd.read_excel(file_obj, skiprows=header_idx)
    
    # 2. Filter: Only keep valid Stock IDs (exclude 'Grand Total' and empty)
    df = df[df['Stk Code'].notna() & (df['Stk Code'] != 'Grand Total:')]
    
    # 3. Select only numeric metrics for comparison
    metrics = ['Prev. Qty', 'In Qty', 'Transfer', 'Transform', 'Issue Qty', 'Del. Qty', 'Bal Qty']
    for m in metrics:
        df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0)
        
    return df.set_index('Stk Code')[metrics]

if file_old and file_new:
    df1 = process_file(file_old)
    df2 = process_file(file_new)
    
    # Compare
    diff = df2 - df1
    # Identify items where any metric changed
    changed = diff[(diff != 0).any(axis=1)]
    
    if not changed.empty:
        st.error(f"Found {len(changed)} modified items:")
        st.dataframe(changed, use_container_width=True)
    else:
        st.success("Files are identical!")
