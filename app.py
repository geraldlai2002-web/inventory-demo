import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Dynamic Inventory Tracker", layout="wide")

st.title("🕵️‍♂️ Multi-Row Inventory Tracker")

# 1. Dynamic File Input Management
if 'file_count' not in st.session_state:
    st.session_state.file_count = 2  # Start with 2 slots

def add_file_row():
    st.session_state.file_count += 1

st.button("➕ Add Another File Row", on_click=add_file_row)

file_uploaders = []
for i in range(st.session_state.file_count):
    file_uploaders.append(st.file_uploader(f"File {i+1} (Row {i+1})", type=["xlsx", "csv"], key=f"file_{i}"))

def parse_stock_sheet(file_obj):
    """Parses file and returns a dictionary of metrics."""
    if not file_obj: return {}
    try:
        df = pd.read_csv(file_obj) if file_obj.name.endswith('.csv') else pd.read_excel(file_obj)
        # Assuming simple structure for comparison
        # You can adjust header search logic here if needed
        data_matrix = {}
        for _, row in df.iterrows():
            stk_code = str(row.iloc[0]).strip()
            if stk_code and stk_code.lower() != 'nan':
                # Map columns (assuming index 1 onwards are numeric metrics)
                metrics = {str(col): float(val) if isinstance(val, (int, float)) else 0.0 
                           for col, val in row.iloc[1:].items()}
                data_matrix[stk_code] = metrics
        return data_matrix
    except:
        return {}

# 2. Comparison Logic
uploaded_files = [f for f in file_uploaders if f is not None]

if len(uploaded_files) >= 2:
    st.markdown("---")
    st.subheader("⚡ Discrepancy Analysis")
    
    # Parse all files
    all_parsed = [parse_stock_sheet(f) for f in uploaded_files]
    baseline = all_parsed[0]
    
    comparison_results = []
    
    # Compare each subsequent file against the baseline
    for idx, current_data in enumerate(all_parsed[1:], start=2):
        for stk_id, metrics in current_data.items():
            baseline_metrics = baseline.get(stk_id, {})
            
            for col, val in metrics.items():
                base_val = baseline_metrics.get(col, 0.0)
                if abs(val - base_val) > 0.01:
                    comparison_results.append({
                        "Stock ID": stk_id,
                        "Metric": col,
                        "Baseline (File 1)": base_val,
                        f"Value (File {idx})": val,
                        "Delta": val - base_val
                    })

    if comparison_results:
        st.error("⚠️ Differences detected against Baseline (File 1):")
        st.dataframe(pd.DataFrame(comparison_results), use_container_width=True)
    else:
        st.success("🎉 All files match the baseline perfectly.")
