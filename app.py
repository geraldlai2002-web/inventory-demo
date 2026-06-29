import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Inventory Delta Tracker", layout="wide")

st.title("🕵️‍♂️ Inventory Audit & Delta Tracker")
st.markdown("### Detect exact Stock ID and Year modifications")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗄️ 1. Historical Individual Year Files (Baseline)")
    baseline_files = st.file_uploader(
        "Upload all individual files (2015_mini, 2016_mini, etc.):", 
        type=["xlsx", "csv"], 
        accept_multiple_files=True, 
        key="baseline"
    )

with col2:
    st.subheader("📥 2. New Combined Multi-Year File")
    new_master_file = st.file_uploader(
        "Upload the new combined 2015_2025 file:", 
        type=["xlsx", "csv"], 
        key="new_master"
    )

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
        
        # Avoid category grouping lines/totals (like PMAT headers or Grand Totals)
        if not stk_code or stk_code.lower() in ['nan', 'grand total:', 'grand total'] or len(stk_code) < 3:
            continue
            
        # Extract row metrics
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

if baseline_files and new_master_file:
    st.markdown("---")
    st.subheader("⚡ Discrepancy Execution Log")
    
    # 1. Parse all individual baseline years
    yearly_db = {}
    expected_combined = {}
    
    for f in baseline_files:
        year_match = re.search(r'(20\d{2})', f.name)
        if not year_match:
            continue
        year = int(year_match.group(1))
        
        file_data = parse_stock_sheet(f)
        yearly_db[year] = file_data
        
        # Accumulate to create the combined expected data
        for stk_id, metrics in file_data.items():
            if stk_id not in expected_combined:
                expected_combined[stk_id] = {k: 0.0 for k in metrics}
            for k, val in metrics.items():
                expected_combined[stk_id][k] += val

    # 2. Parse the newly uploaded combined master file
    new_combined_data = parse_stock_sheet(new_master_file)
    
    # 3. Track down differences row-by-column
    changes_found = []
    all_stock_ids = set(expected_combined.keys()) | set(new_combined_data.keys())
    
    for stk_id in sorted(all_stock_ids):
        old_metrics = expected_combined.get(stk_id, {})
        new_metrics = new_combined_data.get(stk_id, {})
        
        # Check every metric column
        all_columns = set(old_metrics.keys()) | set(new_metrics.keys())
        for col in all_columns:
            old_val = old_metrics.get(col, 0.0)
            new_val = new_metrics.get(col, 0.0)
            
            if abs(old_val - new_val) > 0.01:  # Variance found!
                variance = new_val - old_val
                
                # Trace back which year matches this variance pattern or holds this item
                suspected_year = "Unknown / Multiple Years"
                for year, year_items in yearly_db.items():
                    if stk_id in year_items and abs(year_items[stk_id].get(col, 0.0)) > 0:
                        # If a single year baseline contains this structural record stream, flag it
                        suspected_year = f"{year}"
                
                changes_found.append({
                    "Stock ID": stk_id,
                    "Column Metric": col,
                    "Expected Baseline": f"{old_val:,.2f}",
                    "New Master Value": f"{new_val:,.2f}",
                    "Delta Variance": f"{variance:+,.2f}",
                    "Identified Year": suspected_year
                })

    # Display results
    if changes_found:
        st.error("⚠️ Modified items detected between baseline logs and your new master file:")
        df_changes = pd.DataFrame(changes_found)
        st.dataframe(df_changes, use_container_width=True)
    else:
        st.success("🎉 **Clean Pass:** The new multi-year combined file matches all old historical entries perfectly.")
