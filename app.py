import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Vertical Inventory Tracker", layout="wide")

st.title("🕵️‍♂️ Vertical Inventory Delta Tracker")

# Initialize session state for file slots
if 'baseline_files' not in st.session_state: st.session_state.baseline_files = [None]
if 'compare_files' not in st.session_state: st.session_state.compare_files = [None]

def parse_stock_sheet(file_obj):
    """Parses a file and extracts all metrics for every Stock ID row."""
    if not file_obj: return {}
    try:
        df = pd.read_csv(file_obj) if file_obj.name.endswith('.csv') else pd.read_excel(file_obj, header=None)
    except Exception:
        return {}

    data_matrix = {}
    header_idx = None
    
    # Locate header row (looking for key identifiers)
    for idx in range(min(len(df), 20)):
        row_str = df.iloc[idx].astype(str).str.strip().str.lower().tolist()
        if 'stk code' in row_str or 'in qty' in row_str:
            header_idx = idx
            break
    if header_idx is None: return {}
        
    headers = df.iloc[header_idx].astype(str).str.strip().tolist()
    target_cols = ['Prev. Qty', 'In Qty', 'Transfer', 'Transform', 'Issue Qty', 'Del. Qty', 'Bal Qty']
    col_mapping = {c: headers.index(c) for c in target_cols if c in headers}
            
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

# UI Layout
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("⬅️ Baseline Source")
    if st.button("Add Baseline Row"): st.session_state.baseline_files.append(None)
    for i in range(len(st.session_state.baseline_files)):
        st.session_state.baseline_files[i] = st.file_uploader(f"Baseline {i+1}", key=f"base_{i}")

with right_col:
    st.subheader("➡️ Comparison Files")
    if st.button("Add Comparison Row"): st.session_state.compare_files.append(None)
    for i in range(len(st.session_state.compare_files)):
        st.session_state.compare_files[i] = st.file_uploader(f"Comparison {i+1}", key=f"comp_{i}")

st.markdown("---")
st.subheader("⚡ Discrepancy Execution Log")

if st.button("Run Comparison"):
    # Compare row N to row N
    for i in range(min(len(st.session_state.baseline_files), len(st.session_state.compare_files))):
        base_file = st.session_state.baseline_files[i]
        comp_file = st.session_state.compare_files[i]
        
        if base_file and comp_file:
            st.markdown(f"### 📊 Results: Baseline {i+1} vs Comparison {i+1}")
            base_data = parse_stock_sheet(base_file)
            comp_data = parse_stock_sheet(comp_file)
            
            diffs = []
            all_keys = set(base_data.keys()) | set(comp_data.keys())
            
            for stk_id in sorted(all_keys):
                old, new = base_data.get(stk_id, {}), comp_data.get(stk_id, {})
                for metric in set(old.keys()) | set(new.keys()):
                    val_o, val_n = old.get(metric, 0.0), new.get(metric, 0.0)
                    if abs(val_n - val_o) > 0.01:
                        diffs.append({"Stock ID": stk_id, "Metric": metric, "Baseline": val_o, "New": val_n, "Delta": val_n - val_o})
            
            if diffs:
                st.dataframe(pd.DataFrame(diffs), use_container_width=True)
            else:
                st.success(f"✅ Baseline {i+1} and Comparison {i+1} are identical.")
