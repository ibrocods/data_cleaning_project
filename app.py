import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Interactive Data Cleaner", layout="wide")

st.title("🧼 Interactive Data Cleaning Tool")
st.markdown("""
Welcome to your personal data cleaning consultant! This tool helps you identify and fix common issues in your datasets.
Upload a CSV file to get started.
""")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")


if uploaded_file is not None:
    # Load data
    df = pd.read_csv(uploaded_file)
    original_filename = uploaded_file.name
    base_name, ext = os.path.splitext(original_filename)
    
    st.subheader("📊 Data Preview")
    st.write(f"Dataset contains **{df.shape[0]}** rows and **{df.shape[1]}** columns.")
    st.dataframe(df.head(10))
    
    # Store the dataframe in session state to persist changes
    if 'df' not in st.session_state:
        st.session_state.df = df.copy()
        st.session_state.original_df = df.copy()
        st.session_state.cleaning_log = []

    # --- DATA QUALITY REPORT ---
    st.divider()
    st.subheader("🔍 Data Quality Report")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. Missing Values
    missing_data = st.session_state.df.isnull().sum()
    total_missing = missing_data.sum()
    with col1:
        st.metric("Total Missing Values", total_missing)
        if total_missing > 0:
            st.write("Missing values per column:")
            st.write(missing_data[missing_data > 0])
            
    # 2. Duplicates
    duplicate_count = st.session_state.df.duplicated().sum()
    with col2:
        st.metric("Duplicate Rows", duplicate_count)
        
    # 3. Structural Issues (Whitespace)
    # Check for leading/trailing whitespace in string columns
    string_cols = st.session_state.df.select_dtypes(include=['object']).columns
    whitespace_issues = 0
    for col in string_cols:
        whitespace_issues += st.session_state.df[col].apply(lambda x: len(str(x)) != len(str(x).strip()) if pd.notnull(x) else False).sum()
    
    with col3:
        st.metric("Whitespace Issues", whitespace_issues)

    # --- INTERACTIVE CLEANING ---
    st.divider()
    st.subheader("🛠️ Interactive Cleaning")
    
    # 1. Handle Duplicates
    if duplicate_count > 0:
        st.warning(f"Found {duplicate_count} duplicate rows.")
        if st.button("🗑️ Remove All Duplicates"):
            st.session_state.df.drop_duplicates(inplace=True)
            st.session_state.cleaning_log.append(f"Removed {duplicate_count} duplicate rows.")
            st.success("Duplicates removed!")
            st.rerun()
    
    # 2. Handle Whitespace
    if whitespace_issues > 0:
        st.warning(f"Found {whitespace_issues} cells with extra whitespace.")
        if st.button("✨ Trim All Whitespace"):
            for col in string_cols:
                st.session_state.df[col] = st.session_state.df[col].str.strip()
            st.session_state.cleaning_log.append(f"Trimmed whitespace in {whitespace_issues} cells.")
            st.success("Whitespace trimmed!")
            st.rerun()

    # 3. Handle Missing Values (Column by Column)
    if total_missing > 0:
        st.info("Handle missing values for specific columns:")
        cols_with_missing = missing_data[missing_data > 0].index.tolist()
        
        for col in cols_with_missing:
            with st.expander(f"Missing values in '{col}' ({missing_data[col]} found)"):
                is_numeric = pd.api.types.is_numeric_dtype(st.session_state.df[col])
                
                options = ["Select an action...", "Delete rows with missing values"]
                if is_numeric:
                    options.extend(["Fill with Mean", "Fill with Median"])
                else:
                    options.append("Fill with Mode (Most Frequent)")
                options.append("Fill with Custom Value")
                
                action = st.selectbox(f"Action for '{col}'", options, key=f"action_{col}")
                
                custom_val = None
                if action == "Fill with Custom Value":
                    custom_val = st.text_input(f"Enter custom value for '{col}'", key=f"custom_{col}")
                
                if st.button(f"Apply to '{col}'", key=f"btn_{col}"):
                    if action == "Delete rows with missing values":
                        count_before = len(st.session_state.df)
                        st.session_state.df.dropna(subset=[col], inplace=True)
                        count_after = len(st.session_state.df)
                        st.session_state.cleaning_log.append(f"Deleted {count_before - count_after} rows due to missing values in '{col}'.")
                    elif action == "Fill with Mean":
                        val = st.session_state.df[col].mean()
                        st.session_state.df[col].fillna(val, inplace=True)
                        st.session_state.cleaning_log.append(f"Filled missing values in '{col}' with mean ({val:.2f}).")
                    elif action == "Fill with Median":
                        val = st.session_state.df[col].median()
                        st.session_state.df[col].fillna(val, inplace=True)
                        st.session_state.cleaning_log.append(f"Filled missing values in '{col}' with median ({val}).")
                    elif action == "Fill with Mode (Most Frequent)":
                        val = st.session_state.df[col].mode()[0]
                        st.session_state.df[col].fillna(val, inplace=True)
                        st.session_state.cleaning_log.append(f"Filled missing values in '{col}' with mode ({val}).")
                    elif action == "Fill with Custom Value" and custom_val is not None:
                        st.session_state.df[col].fillna(custom_val, inplace=True)
                        st.session_state.cleaning_log.append(f"Filled missing values in '{col}' with custom value: {custom_val}.")
                    
                    if action != "Select an action...":
                        st.success(f"Applied action to '{col}'!")
                        st.rerun()

    # --- SUMMARY & DOWNLOAD ---
    st.divider()
    st.subheader("🏁 Final Summary & Download")
    
    if st.session_state.cleaning_log:
        st.write("Actions taken so far:")
        for log in st.session_state.cleaning_log:
            st.write(f"- {log}")
        
        # Download button
        csv = st.session_state.df.to_csv(index=False).encode('utf-8')
        cleaned_filename = f"{base_name}_cleaned{ext}"
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv,
            file_name=cleaned_filename,
            mime="text/csv",
        )
        
        if st.button("🔄 Reset All Changes"):
            st.session_state.df = st.session_state.original_df.copy()
            st.session_state.cleaning_log = []
            st.rerun()
    else:
        st.write("No cleaning actions taken yet.")

else:
    st.info("Please upload a CSV file to begin the analysis.")
