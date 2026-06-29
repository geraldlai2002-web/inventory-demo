import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventory Auditor", layout="centered")

st.title("📊 Historical Inventory Auditor")
st.markdown("### Zero-ERP Pure Upload Prototype (2015 - 2025)")

st.write("Upload your official database records on the left, and upload your new audit files on the right to instantly check for discrepancies.")

# --- CREATE TWO COLUMNS FOR CLEAN UPLOADING ---
col1, col2 = st.columns(2)

# --- ZONE 1: OFFICIAL APP RECORDS ---
with col1:
    st.subheader("🗄️ 1. Official Database Data")
    db_files = st.file_uploader(
        "Upload your baseline/approved Excel files here:",
        type=["xlsx"],
        accept_multiple_files=True,
        key="db_uploader"
    )

# --- ZONE 2: NEW AUDIT FILES ---
with col2:
    st.subheader("📥 2. New Files to Audit")
    audit_files = st.file_uploader(
        "Upload the new files you want to verify here:",
        type=["xlsx"],
        accept_multiple_files=True,
        key="audit_uploader"
    )

# --- HELPER FUNCTION TO READ BATCH EXCEL FILES ---
def process_excel_batch(file_list):
    totals_map = {}
    errors = []
    for f in file_list:
        try:
            df = pd.read_excel(f)
            if 'Year' in df.columns and 'Qty' in df.columns:
                file_year = int(df['Year'].iloc[0])
                file_qty_sum = int(df['Qty'].sum())
                totals_map[file_year] = file_qty_sum
            else:
                errors.append(f" `{f.name}` is missing 'Year' or 'Qty' columns.")
        except Exception as e:
            errors.append(f" Error reading `{f.name}`: {str(e)}")
    return totals_map, errors

# --- RUN EXECUTION IF FILES ARE PRESENT IN BOTH ZONES ---
if db_files and audit_files:
    st.markdown("---")
    st.subheader("🔍 Auditor Analysis Run")
    
    # Process both sides
    db_totals, db_errors = process_excel_batch(db_files)
    audit_totals, audit_errors = process_excel_batch(audit_files)
    
    # Print out data parsing formatting errors if any exist
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
                st.success(f"✅ **Year {year}:** Totals match perfectly ({official_val} units). Clean!")
            else:
                st.warning(f"⚠️ **Year {year}:** MISMATCH! DB Record: {official_val} | Uploaded: {uploaded_val} ({diff:+} units)")
                mismatched_years.append(year)
                
        # --- DECISION DISPLAY LOGIC ---
        st.write("───")
        if not mismatched_years:
            st.success("🎉 **Audit Complete:** Every single year matches up perfectly. No historical data entry errors detected!")
        elif len(mismatched_years) == 1:
            st.info(f"💡 **System Action [Scenario 1]:** Discrepancy isolated strictly to **Year {mismatched_years[0]}**. Rest of historical data branches remain completely safe.")
        else:
            st.error(f"🚨 **System Action [Scenario 2]:** Multiple historical records are out of sync: {mismatched_years}. Automatic overwrite disabled to preserve log integrity.")
            
elif db_files or audit_files:
    st.info("☝️ Please make sure you drop files into **BOTH** upload zones above to start the comparison processing.")
