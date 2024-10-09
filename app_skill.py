import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO


# Function to find the page with the "Skill-based Summary" header
def find_skill_summary_page(pdf):
    for i in range(4, 8):  # Page indices for pages 5 to 8
        try:
            page = pdf.pages[i]
            text = page.extract_text()
            if text and "Skill-based Summary" in text:
                return i
        except IndexError:
            # If the page does not exist in the PDF
            break
    return None

# Function to extract data from a single PDF
def extract_data_from_pdf(uploaded_file):
    
    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        # Find the page containing "Skill-based Summary"
        page_number = find_skill_summary_page(pdf)
        if page_number is None:
            st.warning("Skill-based Summary not found in the PDF.")
            return pd.DataFrame()  # Return an empty DataFrame if not found
        
        # Extract the table from the identified page
        page = pdf.pages[page_number]
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
        
        # Extract information from the uploaded file name
        filename = uploaded_file.name
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
st.title("Skill Based Summary")

# Upload PDFs
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        # Extract data from each uploaded PDF file
        df = extract_data_from_pdf(uploaded_file)
        if not df.empty:
            dfs.append(df)
    
    # Concatenate all DataFrames into a single DataFrame
    if dfs:
        final_df = pd.concat(dfs, index=False)

        # Display the DataFrame
        st.dataframe(final_df)

        excel_file_path="Skill Summary.xlsx"
        # Convert DataFrame to Excel
        final_df.to_excel(excel_file_path,ignore_index=True)

        # Download button for the Excel file
        st.download_button(
            label="Download Excel File",
            data=open(excel_file_path, "rb").read(),
            file_name="Skill Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No valid tables found in the uploaded PDFs.")
