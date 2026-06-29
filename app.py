import streamlit as st

st.set_page_config(page_title="Inventory Auditor", layout="centered")

st.title("📊 Historical Inventory Auditor")
st.markdown("### Zero-ERP Concept Prototype (2015 - 2025)")

# --- 1. THE APP'S SAVED DATABASE MEMORY (2015 to 2025) ---
# Simulating the original 5-row total for EVERY year
if 'db_memory' not in st.session_state:
    st.session_state.db_memory = {
        2015: 50,
        2016: 55,
        2017: 58,
        2018: 60,
        2019: 62,
        2020: 65,  # Original 2020 total
        2021: 70,
        2022: 72,
        2023: 75,
        2024: 78,
        2025: 80
    }

# Calculate what the app expects the grand total to be
expected_grand_total = sum(st.session_state.db_memory.values())

# --- SIDEBAR DISPLAY ---
st.sidebar.header("🗄️ App Internal Database")
st.sidebar.markdown("**Expected Yearly Breakdown:**")
for year, qty in st.session_state.db_memory.items():
    st.sidebar.write(f"Year {year}: {qty} units")
st.sidebar.write(f"───")
st.sidebar.write(f"**Expected Grand Total:** {expected_grand_total} units")

st.write("This app simulates reading a single 10-year cumulative master file and catching backdated tampering automatically.")

# --- 2. CHOOSE DEMO SCENARIO ---
st.subheader("Step 1: Select Demo Scenario")
scenario = st.selectbox(
    "Choose what the staff changed in the master data to test the system:",
    ["Select a scenario...", 
     "No Changes (Data is perfectly synced)", 
     "Scenario 1: Staff secretly changed ONE year (2020 Qty +45)", 
     "Scenario 2: Staff secretly changed TWO years (2016 Qty +20, 2020 Qty +45)"]
)

# --- 3. THE MATH DETECTIVE ENGINE ---
if scenario != "Select a scenario...":
    st.subheader("Step 2: App Processing Results")
    
    # Create a base copy of the clean data
    uploaded_totals = st.session_state.db_memory.copy()
    
    # Inject scenario changes
    if scenario == "No Changes (Data is perfectly synced)":
        pass
    elif scenario == "Scenario 1: Staff secretly changed ONE year (2020 Qty +45)":
        uploaded_totals[2020] = 110  # 65 + 45
    elif scenario == "Scenario 2: Staff secretly changed TWO years (2016 Qty +20, 2020 Qty +45)":
        uploaded_totals[2016] = 75   # 55 + 20
        uploaded_totals[2020] = 110  # 65 + 45
        
    uploaded_grand_total = sum(uploaded_totals.values())
    st.write(f"📁 **Uploaded File Grand Total:** {uploaded_grand_total} units")
    
    # Calculate Overall Discrepancy
    total_difference = uploaded_grand_total - expected_grand_total
    
    if total_difference == 0:
        st.success("✅ **Success:** Uploaded grand total matches app memory perfectly. No historical data was tampered with!")
    else:
        st.warning(f"⚠️ **Discrepancy Detected:** Overall grand total is off by **{total_difference:+} units**.")
        st.write("Peeling back database history layers to isolate the source...")
        
        # Check individual years
        mismatched_years = []
        for year in sorted(st.session_state.db_memory.keys()):
            if uploaded_totals[year] != st.session_state.db_memory[year]:
                mismatched_years.append(year)
                
        # --- SCENARIO 1 UI CONTROL ---
        if len(mismatched_years) == 1:
            target_year = mismatched_years[0]
            yearly_diff = uploaded_totals[target_year] - st.session_state.db_memory[target_year]
            st.success(f"🎯 **Target Isolated!** The entire discrepancy belongs strictly to **Year {target_year}** ({yearly_diff:+} units).")
            
            if st.button(f"Auto-Sync Year {target_year} Memory"):
                st.session_state.db_memory[target_year] = uploaded_totals[target_year]
                st.success("Database updated successfully!")
                st.rerun()
                
        # --- SCENARIO 2 UI CONTROL ---
        elif len(mismatched_years) > 1:
            st.error(f"🚨 **Mathematical Deadlock:** Mismatches detected across multiple historical branches: {mismatched_years}.")
        
