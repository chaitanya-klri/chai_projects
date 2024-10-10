import streamlit as st
import pdfplumber
import pandas as pd
import re
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

# Function to extract the year from the footer of the PDF pages
def extract_year_from_footer(pdf):
    for page in pdf.pages:
        # Get the height and width of the page to target the footer area
        page_height = page.height
        page_width = page.width
        
        # Define a box at the bottom of the page to extract footer text
        footer_box = (0, page_height - 50, page_width, page_height)
        footer_text = page.within_bbox(footer_box).extract_text()
        
        # Check if there's text in the footer that might contain the year
        if footer_text:
            # Look for a year pattern (e.g., 2020, 2021, etc.)
            match = re.search(r"\b(20\d{2})\b", footer_text)
            if match:
                year = match.group(0)
                st.write("Extracted Year:", year)  # Debug print for the extracted year
                return year
    return None

# Function to extract school code, subject, class, and section from the footer
def extract_info_from_footer(pdf):
    for page in pdf.pages:
        # Get the height and width of the page to target the footer area
        page_height = page.height
        page_width = page.width
        
        # Define a box at the bottom of the page to extract footer text
        footer_box = (0, page_height - 50, page_width, page_height)
        footer_text = page.within_bbox(footer_box).extract_text()
        
        # Check if the footer contains the pattern for school code and details (e.g., "2565760/E3A")
        if footer_text:
            match = re.search(r"(\d+)/([A-Z])(\d{1,2})([A-Z])", footer_text)
            if match:
                school_code = match.group(1)
                subject_code = match.group(2)
                class_value = match.group(3)
                section = match.group(4)
                
                # Determine the subject based on the subject code
                if subject_code == 'E':
                    subject = 'English'
                elif subject_code == 'M':
                    subject = 'Maths'
                elif subject_code == 'S':
                    subject = 'Science'
                else:
                    subject = 'Unknown'
                
                return school_code, subject, class_value, section
    return None, None, None, None

# Function to extract data from a single PDF
def extract_data_from_pdf(uploaded_file):
    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        # Extract the year from the footer
        year = extract_year_from_footer(pdf)
        if not year:
            st.warning("Year not found in the PDF footer.")
            return pd.DataFrame()  # Return an empty DataFrame if the year is not found
        
        # Extract school code, subject, class, and section from the footer
        school_code, subject, class_value, section = extract_info_from_footer(pdf)
        if not school_code or not subject or not class_value or not section:
            st.warning("School code, subject, class, or section not found in the PDF footer.")
            return pd.DataFrame()  # Return an empty DataFrame if any of the information is missing
        
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
        
        # Add columns to the DataFrame
        df['School Code'] = school_code
        df['Subject'] = subject
        df['Class'] = class_value
        df['Section'] = section
        df['Year'] = year  # Add the extracted year here
        
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
        final_df = pd.concat(dfs, ignore_index=True)

        # Display the DataFrame
        st.dataframe(final_df)

        excel_file_path = "Skill Summary.xlsx"
        # Convert DataFrame to Excel
        final_df.to_excel(excel_file_path, index=False)

        # Download button for the Excel file
        st.download_button(
            label="Download Excel File",
            data=open(excel_file_path, "rb").read(),
            file_name="Skill Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No valid tables found in the uploaded PDFs.")
