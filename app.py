import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Vertical Inventory Tracker", layout="wide")

st.title("🕵️‍♂️ Vertical Inventory Delta Tracker")

# Create two vertical main containers
left_col, right_col = st.columns(2)

# Session state to manage inputs for each side
if 'baseline_files' not in st.session_state: st.session_state.baseline_files = [None]
if 'compare_files' not in st.session_state: st.session_state.compare_files = [None]

with left_col:
    st.subheader("⬅️ Baseline Source")
    if st.button("Add Baseline Slot"): st.session_state.baseline_files.append(None)
    for i in range(len(st.session_state.baseline_files)):
        st.session_state.baseline_files[i] = st.file_uploader(f"Baseline File {i+1}", key=f"base_{i}")

with right_col:
    st.subheader("➡️ Comparison Files")
    if st.button("Add Comparison Slot"): st.session_state.compare_files.append(None)
    for i in range(len(st.session_state.compare_files)):
        st.session_state.compare_files[i] = st.file_uploader(f"Comparison File {i+1}", key=f"comp_{i}")

def parse_data(file_obj):
    # Reusing your existing robust parsing logic
    if not file_obj: return {}
    # ... [Keep your parse_stock_sheet logic here] ...
    return {} # Placeholder for your specific parsing function

st.markdown("---")
st.subheader("⚡ Discrepancy Execution Log")

# 3. Execution Logic
if st.button("Run Comparison"):
    st.markdown("---")
    # Loop through the pairs
    for i in range(min(len(st.session_state.baseline_files), len(st.session_state.compare_files))):
        base_file = st.session_state.baseline_files[i]
        comp_file = st.session_state.compare_files[i]
        
        if base_file and comp_file:
            st.subheader(f"📊 Results: Baseline {i+1} vs Comparison {i+1}")
            
            # Parse files
            base_data = parse_stock_sheet(base_file)
            comp_data = parse_stock_sheet(comp_file)
            
            # Logic to find differences
            differences = []
            all_keys = set(base_data.keys()) | set(comp_data.keys())
            
            for stk_id in sorted(all_keys):
                old = base_data.get(stk_id, {})
                new = comp_data.get(stk_id, {})
                
                # Check metrics (assuming same columns in both)
                for metric in set(old.keys()) | set(new.keys()):
                    val_old = old.get(metric, 0.0)
                    val_new = new.get(metric, 0.0)
                    
                    if abs(val_new - val_old) > 0.01:
                        differences.append({
                            "Stock ID": stk_id,
                            "Metric": metric,
                            "Baseline": f"{val_old:,.2f}",
                            "New": f"{val_new:,.2f}",
                            "Delta": f"{val_new - val_old:+,.2f}"
                        })
            
            # Display result for this specific pair
            if differences:
                st.dataframe(pd.DataFrame(differences), use_container_width=True)
            else:
                st.success(f"✅ Baseline {i+1} and Comparison {i+1} are identical.")
