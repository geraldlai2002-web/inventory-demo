import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Inventory Auditor", layout="centered")

st.title("📊 Historical Inventory Auditor")
st.markdown("### Sumirubber Stock Movement Auditor")

st.write("Drop your **Master 2015_2025 file** on the left, and your **Individual Yearly files** on the right.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗄️ 1. Master Database File")
    db_files = st.file_uploader("Upload Master 2015_2025 Excel:", type=["xlsx"], accept_multiple_files=True, key="db_uploader")

with col2:
    st.subheader("📥 2. Individual Yearly Files")
    audit_files = st.file_uploader("Upload yearly verification files:", type=["xlsx"], accept_multiple_files=True, key="audit_uploader")

def get_grand_total_from_sheet(df_raw, header_row_idx, in_qty_col_idx):
    for idx in range(len(df_raw)):
        row_cells = df_raw.iloc[idx].dropna().astype(str).str.strip().tolist()
        row_text_joined = " ".join(row_cells).lower()
        if 'grand total' in row_text_joined:
            val_str = ""
            if in_qty_col_idx < len(df_raw.iloc[idx]):
                val_str = str(df_raw.iloc[idx, in_qty_col_idx]).strip()
            val_clean = re.sub(r'[^\d.-]', '', val_str)
            if not val_clean or val_clean == 'nan':
                for cell in reversed(row_cells):
                    possible_val = re.sub(r'[^\d.-]', '', cell)
                    if possible_val and possible_val != '.':
                        val_clean = possible_val
                        break
            if val_clean:
                return int(float(val_clean))
    return None

def process_files(db_list, audit_list):
    db_totals = {}
    audit_totals = {}
    errors = []
    
    # 1. Process Master File(s) on Left
    for f in db_list:
        try:
            # If it's a multi-sheet master or single sheet, read it
            xl = pd.ExcelFile(f)
            for sheet_name in xl.sheet_names:
                # Find year from sheet name or filename
                year_match = re.search(r'(20\d{2})', sheet_name) or re.search(r'(20\d{2})', f.name)
                if not year_match:
                    continue
                year = int(year_match.group(1))
                
                df_raw = pd.read_excel(f, sheet_name=sheet_name, header=None)
                header_row_idx = None
                for idx in range(min(len(df_raw), 15)):
                    row_items = df_raw.iloc[idx].astype(str).str.strip().str.lower().tolist()
                    if 'stk code' in row_items or 'in qty' in row_items:
                        header_row_idx = idx
                        break
                if header_row_idx is not None:
                    headers = df_raw.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist()
                    in_qty_idx = headers.index('in qty') if 'in qty' in headers else None
                    if in_qty_idx is not None:
                        g_total = get_grand_total_from_sheet(df_raw, header_row_idx, in_qty_idx)
                        if g_total is not None:
                            db_totals[year] = g_total
        except Exception as e:
            errors.append(f"❌ Error reading master `{f.name}`: {str(e)}")

    # 2. Process Yearly Files on Right
    for f in audit_list:
        try:
            year_match = re.search(r'(20\d{2})', f.name)
            if not year_match:
                errors.append(f"❌ No 4-digit year in filename `{f.name}`.")
                continue
            year = int(year_match.group(1))
            
            df_raw = pd.read_excel(f, header=None)
            header_row_idx = None
            for idx in range(min(len(df_raw), 15)):
                row_items = df_raw.iloc[idx].astype(str).str.strip().str.lower().tolist()
                if 'stk code' in row_items or 'in qty' in row_items:
                    header_row_idx = idx
                    break
            if header_row_idx is not None:
                headers = df_raw.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist()
                in_qty_idx = headers.index('in qty') if 'in qty' in headers else None
                if in_qty_idx is not None:
                    g_total = get_grand_total_from_sheet(df_raw, header_row_idx, in_qty_idx)
                    if g_total is not None:
                        audit_totals[year] = g_total
        except Exception as e:
            errors.append(f"❌ Error reading yearly file `{f.name}`: {str(e)}")
            
    return db_totals, audit_totals, errors

if db_files and audit_files:
    st.markdown("---")
    st.subheader("🔍 Auditor Analysis Run")
    
    db_totals, audit_totals, errors = process_files(db_files, audit_files)
    
    for err in errors:
        st.error(err)
        
    if not errors:
        all_years = sorted(list(set(db_totals.keys()) | set(audit_totals.keys())))
        mismatched_years = []
        
        for year in all_years:
            official_val = db_totals.get(year, 0)
            uploaded_val = audit_totals.get(year, 0)
            diff = uploaded_val - official_val
            
            if diff == 0 and official_val > 0:
                st.success(f"✅ **Year {year}:** 'In Qty' Grand Total matches perfectly ({official_val:,} units).")
            elif official_val == 0 or uploaded_val == 0:
                st.info(f"ℹ️ **Year {year}:** Waiting for matching file on both sides.")
            else:
                sign = "+" if diff > 0 else ""
                st.warning(f"⚠️ **Year {year}:** MISMATCH! Master: {official_val:,} | Yearly: {uploaded_val:,} ({sign}{diff:,} units)")
                mismatched_years.append(year)
                
        st.write("───")
        if all_years and not mismatched_years:
            st.success("🎉 **Audit Complete:** Everything aligns cleanly!")
            
elif db_files or audit_files:
    st.info("☝️ Drop your Master file on the left AND your yearly files on the right to trigger the scan.")
