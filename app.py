import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Inventory Auditor", layout="centered")

st.title("📊 Historical Inventory Auditor")
st.markdown("### Zero-ERP Custom Column Prototype")

st.write("Upload your official database records on the left, and your new audit files on the right. The system reads the year from the filename and sums the **In Qty** column.")

# --- CREATE TWO COLUMNS FOR CLEAN UPLOADING ---
col1, col2 = st.columns(2)

# --- ZONE 1: OFFICIAL APP RECORDS ---
with col1:
    st.subheader("🗄️ 1. Official Database Data")
    db_files = st.file_uploader(
        "Upload baseline Excel files:",
        type=["xlsx"],
        accept_multiple_files=True,
        key="db_uploader"
    )

# --- ZONE 2: NEW AUDIT FILES ---
with col2:
    st.subheader("📥 2. New Files to Audit")
    audit_files = st.file_uploader(
        "Upload verification Excel files:",
        type=["xlsx"],
        accept_multiple_files=True,
        key="audit_uploader"
    )

# --- HELPER FUNCTION TO EXTRACT YEAR FROM FILE NAME & SUM 'IN QTY' ---
def process_warehouse_batch(file_list):
    totals_map = {}
    errors = []
    
    for f in file_list:
        try:
            # 1. Extract the year from the filename (e.g., "2025.xlsx" -> 2025)
            file_name_without_ext = os.path.splitext(f.name)[0]
            # Strip any extra text just in case, extracting digits
            year_digits = "".join(filter(str.isdigit, file_name_without_ext))
            
            if not year_digits:
                errors.append(f"❌ Could not detect a year in the filename `{f.name}`. Please name it like `2025.xlsx`.")
                continue
                
            file_year = int(year_digits)
            
            # 2. Read the Excel sheet
            df = pd.read_excel(f)
            
            # 3. Look for 'In Qty' column dynamically (ignoring case/spaces)
            df.columns = df.columns.str.strip() # Clean whitespaces
            target_col = None
            for col in df.columns:
                if col.lower() == 'in qty':
                    target_col = col
                    break
            
            if target_col is not None:
                # Calculate sum total for 'In Qty', ignoring blank rows
                file_qty_sum = pd.to_numeric(df[target_col], errors='coerce').sum()
                totals_map[file_year] = int(file_qty_sum)
            else:
                errors.append(f"❌ `{f.name}` is missing the exact **'In Qty'** column header.")
        except Exception as e:
            errors.append(f"❌ Error reading `{f.name}`: {str(e)}")
            
    return totals_map, errors

# --- RUN EXECUTION IF FILES ARE PRESENT IN BOTH ZONES ---
if db_files and audit_files:
    st.markdown("---")
    st.subheader("🔍 Auditor Analysis Run")
    
    # Process both sides
    db_totals, db_errors = process_warehouse_batch(db_files)
    audit_totals, audit_errors = process_warehouse_batch(audit_files)
    
    # Print out data parsing errors if any exist
    for err in (db_errors + audit_errors):
        st.error(err)
        
    if not db_errors and not audit_errors:
        # Get all unique years uploaded across both datasets
        all_years = sorted(list(set(db_totals.keys()) | set(audit_totals.keys())))
        
        mismatched_years = []
        
        # Cross-analyze totals side by side
        for year in all_years:
            official_val = db_totals.get(year, 0)
            uploaded_val = audit_totals.get(year, 0)
            diff = uploaded_val - official_val
            
            if diff == 0:
                st.success(f"✅ **Year {year}:** 'In Qty' totals match perfectly ({official_val} units). Clean!")
            else:
                st.warning(f"⚠️ **Year {year}:** MISMATCH! DB Record: {official_val} | Uploaded: {uploaded_val} ({diff:+} units)")
                mismatched_years.append(year)
                
        # --- DECISION DISPLAY LOGIC ---
        st.write("───")
        if not mismatched_years:
            st.success("🎉 **Audit Complete:** Every single year matches up perfectly. No historical data entry errors detected!")
        elif len(mismatched_years) == 1:
            st.info(f"💡 **System Action [Scenario 1]:** Discrepancy isolated strictly to **Year {mismatched_years[0]}** inside 'In Qty' pipeline.")
        else:
            st.error(f"🚨 **System Action [Scenario 2]:** Multiple historical records out of sync: {mismatched_years}. Automatic overwrite disabled.")
            
elif db_files or audit_files:
    st.info("☝️ Please make sure you drop files into **BOTH** upload zones above to start the comparison processing.")
