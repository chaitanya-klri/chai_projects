import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

# Function to extract data from a single PDF
def extract_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Adjust the page number as per your PDF (here assuming page 7)
        page = pdf.pages[6]  # Index starts at 0
        
        # Extract the table from the page
        table = page.extract_table()
    
    # Extract relevant rows and columns
    if table:
        data = []
        for row in table[2:]:
            # Extract the first, second, fifth, and sixth values
            if row[0] is not None:
                data.append([row[0], row[1], row[3], row[4], row[5]])
        
        # Convert to a DataFrame
        df = pd.DataFrame(data, columns=["S.no", "Skill", "Section Performance", "Class Performance", "National Performance"])
        
        # Extract information from the filename
        filename = pdf_path.split('/')[-1]
        parts = filename.split('_')
        
        # Add new columns based on the filename
        school_code = parts[0]
        subject_code = parts[1][0]
        if subject_code == 'E':
            subject = 'English'
        elif subject_code == 'M':
            subject = 'Maths'
        elif subject_code == 'S':
            subject = 'Science'
        else:
            subject = 'Unknown'
        
        # Determine class and section
        if parts[1][1:3] == '10':
            class_value = '10'
            section = parts[1][3]
        else:
            class_value = parts[1][1]
            section = parts[1][2]
        
        # Add columns to the DataFrame
        df['School Code'] = school_code
        df['Subject'] = subject
        df['Class'] = class_value
        df['Section'] = section
        
        return df
    else:
        st.warning("No table found in the PDF.")
        return pd.DataFrame()  # Return an empty DataFrame if no table is found

# Streamlit App
st.title("PDF to Excel Data Extractor")

# Upload PDFs
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        # Read each PDF file
        with BytesIO(uploaded_file.read()) as pdf_file:
            df = extract_data_from_pdf(pdf_file)
            if not df.empty:
                dfs.append(df)
    
    # Concatenate all DataFrames into a single DataFrame
    if dfs:
        final_df = pd.concat(dfs, ignore_index=True)

        # Display the DataFrame
        st.dataframe(final_df)

        # Convert DataFrame to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Skill Summary')
            writer.save()
        output.seek(0)

        # Download button for the Excel file
        st.download_button(
            label="Download Excel File",
            data=output,
            file_name="skill_based_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No valid tables found in the uploaded PDFs.")
