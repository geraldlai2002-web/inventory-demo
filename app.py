import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Inventory Delta Tracker", layout="wide")

st.title("🕵️‍♂️ Inventory Audit & Delta Tracker")
st.markdown("### Detect exact Stock ID and Metric modifications between two files")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗄️ 1. Baseline File")
    baseline_file = st.file_uploader("Upload the original file:", type=["xlsx", "csv"], key="baseline")

with col2:
    st.subheader("📥 2. New File")
    new_file = st.file_uploader("Upload the new file to compare:", type=["xlsx", "csv"], key="new_master")

def parse_stock_sheet(file_obj):
    """Parses a file and extracts all metrics for every Stock ID row."""
    try:
        if file_obj.name.endswith('.csv'):
            df = pd.read_csv(file_obj, header=None)
        else:
            df = pd.read_excel(file_obj, header=None)
    except Exception:
        return {}

    data_matrix = {}
    header_idx = None
    
    # Find the main data table headers
    for idx in range(min(len(df), 20)):
        row_str = df.iloc[idx].astype(str).str.strip().str.lower().tolist()
        if 'stk code' in row_str or 'in qty' in row_str:
            header_idx = idx
            break
            
    if header_idx is None:
        return {}
        
    headers = df.iloc[header_idx].astype(str).str.strip().tolist()
    
    # Target standard report columns
    target_cols = ['Prev. Qty', 'In Qty', 'Transfer', 'Transform', 'Issue Qty', 'Del. Qty', 'Bal Qty']
    col_mapping = {}
    for c in target_cols:
        if c in headers:
            col_mapping[c] = headers.index(c)
            
    # Parse rows starting after the header row
    for idx in range(header_idx + 1, len(df)):
        row = df.iloc[idx]
        stk_code = str(row.iloc[0]).strip()
        
        if not stk_code or stk_code.lower() in ['nan', 'grand total:', 'grand total'] or len(stk_code) < 3:
            continue
            
        item_metrics = {}
        for col_name, col_idx in col_mapping.items():
            try:
                val_raw = str(row.iloc[col_idx]).strip()
                val_clean = re.sub(r'[^\d.-]', '', val_raw)
                item_metrics[col_name] = float(val_clean) if val_clean else 0.0
            except:
                item_metrics[col_name] = 0.0
                
        data_matrix[stk_code] = item_metrics
        
    return data_matrix

if baseline_file and new_file:
    st.markdown("---")
    st.subheader("⚡ Discrepancy Execution Log")
    
    # 1. Parse both files
    baseline_data = parse_stock_sheet(baseline_file)
    new_data = parse_stock_sheet(new_file)
    
    # 2. Track down differences
    changes_found = []
    all_stock_ids = set(baseline_data.keys()) | set(new_data.keys())
    
    for stk_id in sorted(all_stock_ids):
        old_metrics = baseline_data.get(stk_id, {})
        new_metrics = new_data.get(stk_id, {})
        
        all_columns = set(old_metrics.keys()) | set(new_metrics.keys())
        for col in all_columns:
            old_val = old_metrics.get(col, 0.0)
            new_val = new_metrics.get(col, 0.0)
            
            if abs(old_val - new_val) > 0.01:
                variance = new_val - old_val
                
                changes_found.append({
                    "Stock ID": stk_id,
                    "Column Metric": col,
                    "Baseline Value": f"{old_val:,.2f}",
                    "New File Value": f"{new_val:,.2f}",
                    "Delta Variance": f"{variance:+,.2f}"
                })

    if changes_found:
        st.error("⚠️ Modified items detected between the two files:")
        st.dataframe(pd.DataFrame(changes_found), use_container_width=True)
    else:
        st.success("🎉 **Clean Pass:** Both files match perfectly.")
