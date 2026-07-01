import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventory Delta Tracker", layout="wide")
st.title("⚖️ Inventory Delta Tracker")

col1, col2 = st.columns(2)
file_old = col1.file_uploader("Upload Baseline File", type=["csv"])
file_new = col2.file_uploader("Upload New Master File", type=["csv"])

def load_and_sanitize(file_obj):
    # 1. Read the file, skipping the first 6 lines of report metadata
    df = pd.read_csv(file_obj, skiprows=6)
    
    # 2. Filter: Only keep rows where 'Stk Code' starts with 'D'
    # This automatically drops 'PMAT', 'Grand Total', and empty rows
    df = df[df['Stk Code'].astype(str).str.startswith('D', na=False)].copy()
    
    # 3. Clean numeric columns: Remove any non-numeric noise and force to float
    metrics = ['Prev. Qty', 'In Qty', 'Transfer', 'Transform', 'Issue Qty', 'Del. Qty', 'Bal Qty']
    for m in metrics:
        df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0)
        
    return df.set_index('Stk Code')[metrics]

if file_old and file_new:
    try:
        df1 = load_and_sanitize(file_old)
        df2 = load_and_sanitize(file_new)
        
        # Calculate Delta
        diff = df2 - df1
        
        # Find only rows where there is at least one difference
        changed = diff[(diff.abs().sum(axis=1) > 0)]
        
        if not changed.empty:
            st.error(f"⚠️ Found {len(changed)} items with discrepancies:")
            st.dataframe(changed, use_container_width=True)
            
            # Optional: Show a breakdown of what exactly changed
            st.write("### Detailed Variance View")
            st.dataframe(diff.loc[changed.index], use_container_width=True)
        else:
            st.success("✅ Clean Pass: Both files are identical.")
            
    except Exception as e:
        st.error(f"Error processing files: {e}")
        st.info("Check if your files have the same header format.")
