import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Inventory Auditor", layout="centered")

st.title("📊 Historical Inventory Auditor")
st.markdown("### Sumirubber Stock Movement Auditor")

st.write("Upload your files into both columns. The system dynamically reads the exact **Grand Total** value from your reports.")

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
            # 1. Extract the 4-digit year reliably from the file name
            year_match = re.search(r'(20\d{2})', f.name)
            if not year_match:
                errors.append(f"❌ Could not detect a valid 4-digit year in filename `{f.name}`.")
                continue
            file_year = int(year_match.group(1))
            
            # 2. Read raw Excel file
            df_raw = pd.read_excel(f, header=None)
            
            # 3. Find the header row to locate columns dynamically
            header_row_idx = None
            for idx in range(min(len(df_raw), 15)):
                row_items = df_raw.iloc[idx].astype(str).str.strip().str.lower().tolist()
                if 'stk code' in row_items or 'in qty' in row_items:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None:
                errors.append(f"❌ `{f.name}`: Could not identify the stock report data columns row.")
                continue
            
            # Extract header text labels
            headers = df_raw.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist()
            
            # Find which column index is 'in qty'
            in_qty_col_idx = None
            for idx, h in enumerate(headers):
                if h == 'in qty':
                    in_qty_col_idx = idx
                    break
            
            if in_qty_col_idx is None:
                errors.append(f"❌ `{f.name}` is missing the exact **'In Qty'** header column.")
                continue
                
            # 4. Find the 'Grand Total:' row by scanning all cells in each row
            grand_total_val = None
            for idx in range(len(df_raw)):
                row_cells = df_raw.iloc[idx].dropna().astype(str).str.strip().tolist()
                row_text_joined = " ".join(row_cells).lower()
                
                if 'grand total' in row_text_joined:
                    val_str = ""
                    # Safety check: see if the 'In Qty' column position exists on this specific row array
                    if in_qty_col_idx < len(df_raw.iloc[idx]):
                        val_str = str(df_raw.iloc[idx, in_qty_col_idx]).strip()
                    
                    # Fallback: If out of bounds or empty, extract the numbers from the row cells directly
                    val_clean = re.sub(r'[^\d.-]', '', val_str)
                    if not val_clean or val_clean == 'nan':
                        # Scan backwards through the row to find the first valid numeric string
                        for cell in reversed(row_cells):
                            possible_val = re.sub(r'[^\d.-]', '', cell)
                            if possible_val and possible_val != '.':
                                val_clean = possible_val
                                break
                                
                    if val_clean:
                        grand_total_val = int(float(val_clean))
                    break
            
            if grand_total_val is not None:
                totals_map[file_year] = grand_total_val
            else:
                errors.append(f"❌ `{f.name}`: Could not find a 'Grand Total:' summary row at the bottom.")
                
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
                st.success(f"✅ **Year {year}:** 'In Qty' Grand Total matches perfectly ({official_val:,} units).")
            else:
                # Fixed formatting logic here: split sign determination from comma string layout
                sign = "+" if diff > 0 else ""
                st.warning(f"⚠️ **Year {year}:** MISMATCH! DB Record: {official_val:,} | Uploaded: {uploaded_val:,} ({sign}{diff:,} units)")
                mismatched_years.append(year)
                
        st.write("───")
        if not mismatched_years:
            st.success("🎉 **Audit Complete:** Every year matches cleanly based on official Grand Totals!")
        elif len(mismatched_years) == 1:
            st.info(f"💡 **System Action [Scenario 1]:** Discrepancy isolated strictly to **Year {mismatched_years[0]}**.")
        else:
            st.error(f"🚨 **System Action [Scenario 2]:** Multiple historical records out of sync: {mismatched_years}.")
            
elif db_files or audit_files:
    st.info("☝️ Please make sure you drop files into **BOTH** upload zones above to start.")
