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

# Logic: Compare file at index N in Left to file at index N in Right
if st.button("Run Comparison"):
    for i in range(min(len(st.session_state.baseline_files), len(st.session_state.compare_files))):
        base = st.session_state.baseline_files[i]
        comp = st.session_state.compare_files[i]
        
        if base and comp:
            st.write(f"### Comparing Baseline {i+1} vs Comparison {i+1}")
            # Insert your existing comparison logic here
            # This ensures Row 1 is compared to Row 1, Row 2 to Row 2, etc.
