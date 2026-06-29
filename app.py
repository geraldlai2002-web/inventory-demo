import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Inventory Auditor", layout="centered")

st.title("📊 Historical Inventory Auditor")
st.markdown("### Sumirubber Stock Movement Auditor")

st.write("Upload your files into both columns. The system dynamically aligns to the stock movement summary report layout.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗄️ 1. Official Database Data")
    db_files = st.file_uploader("Upload baseline Excel files:", type=["xlsx"], accept_multiple_files=True, key="db_uploader")

with col2:
    st.subheader("📥 2. New Files to Audit")
    audit_files = st.file_uploader("Upload verification Excel files:", type=["xlsx"], accept_multiple_files=True, key="audit_uploader")

def process_warehouse_batch(file_list):
    totals_map = {}
    errors = []
    
    for f in file_list:
        try:
            # 1. Extract the 4-digit year reliably from the file name (e.g., "2025-1-1.xlsx" -> 2025)
            year_match = re.search(r'(20\d{2})', f.name)
            if not year_match:
                errors.append(f"❌ Could not detect a valid 4-digit year in filename `{f.name}`.")
                continue
            file_year = int(year_match.group(1))
            
            # 2. Read raw Excel file
            df_raw = pd.read_excel(f, header=None)
            
            # 3. Find the header row by looking for 'Stk Code' or 'In Qty'
            header_row_idx = None
            for idx in range(min(len(df_raw), 15)):
                row_items = df_raw.iloc[idx].astype(str).str.strip().str.lower().tolist()
                if 'stk code' in row_items or 'in qty' in row_items:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None:
                errors.append(f"❌ `{f.name}`: Could not identify the stock report data columns row.")
                continue
            
            # 4. Set the discovered row as the official columns headers
            df_cleaned = df_raw.iloc[header_row_idx+1:].copy()
            df_cleaned.columns = df_raw.iloc[header_row_idx].astype(str).str.strip()
            
            # 5. Look for the 'In Qty' target column case-insensitively
            target_col = None
            for col in df_cleaned.columns:
                if col.lower() == 'in qty':
                    target_col = col
                    break
            
            if target_col is not None:
                # Filter out rows that are part of the header context or empty summary lines at the bottom
                # Convert the data numbers safely
                qty_series = pd.to_numeric(df_cleaned[target_col], errors='coerce').dropna()
                
                # We divide by 2 because summary sheets often contain a visual 'Grand Total' line at the bottom 
                # that doubles the column sum total.
                total_sum = int(qty_series.sum())
                
                # Check if the last row contains a grand total string to prevent double counting
                last_row_strings = df_cleaned.iloc[-1].astype(str).str.lower().values
                if any('grand total' in x for x in last_row_strings):
                    # Strip the final grand total element calculation so rows don't double sum
                    total_sum = total_sum // 2
                    
                totals_map[file_year] = total_sum
            else:
                errors.append(f"❌ `{f.name}` is missing the exact **'In Qty'** header row.")
                
        except Exception as e:
            errors.append(f"❌ Error reading `{f.name}`: {str(e)}")
            
    return totals_map, errors

if db_files and audit_files:
    st.markdown("---")
    st.subheader("🔍 Auditor Analysis Run")
    
    db_totals, db_errors = process_warehouse_batch(db_files)
    audit_totals, audit_errors = process_warehouse_batch(audit_files)
    
    for err in (db_errors + audit_errors):
        st.error(err)
        
    if not db_errors and not audit_errors:
        all_years = sorted(list(set(db_totals.keys()) | set(audit_totals.keys())))
        mismatched_years = []
        
        for year in all_years:
            official_val = db_totals.get(year, 0)
            uploaded_val = audit_totals.get(year, 0)
            diff = uploaded_val - official_val
            
            if diff == 0:
                st.success(f"✅ **Year {year}:** 'In Qty' matches perfectly ({official_val:,} units).")
            else:
                st.warning(f"⚠️ **Year {year}:** MISMATCH! DB Record: {official_val:,} | Uploaded: {uploaded_val:,} ({diff:+:,} units)")
                mismatched_years.append(year)
                
        st.write("───")
        if not mismatched_years:
            st.success("🎉 **Audit Complete:** Records align cleanly across all processed report lines!")
        elif len(mismatched_years) == 1:
            st.info(f"💡 **System Action [Scenario 1]:** Discrepancy isolated strictly to **Year {mismatched_years[0]}**.")
        else:
            st.error(f"🚨 **System Action [Scenario 2]:** Multiple historical records out of sync: {mismatched_years}.")
            
elif db_files or audit_files:
    st.info("☝️ Please make sure you drop files into **BOTH** upload zones above to start.")
