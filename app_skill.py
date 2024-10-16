import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO


# Function to find the page with the "Skill-based Summary" header
def find_skill_summary_page(pdf):
    # st.write("Calling find_skill_summary_page")  # Debug statement
    for i in range(4, 8):  # Page indices for pages 5 to 8
        try:
            page = pdf.pages[i]
            text = page.extract_text()
            if text and "Skill-based Summary" in text:
                # st.write("Skill-based Summary found on page:", i + 1)  # Debug statement
                return i
        except IndexError:
            break
    st.write("Skill-based Summary not found")  # Debug statement
    return None

# Function to extract the year based on specific terms (e.g., "Summer 2023")
def extract_year_from_pdf(pdf):
    # Define the patterns to search for, including month-year patterns
    patterns = [
        r"Summer 2023", r"Winter 2023",
        r"Summer 2024", r"Winter 2024",
        r"Summer 2022", r"Winter 2022",

        # Month-year combinations
        r"January \d{4}", r"February \d{4}", r"March \d{4}", r"April \d{4}",
        r"May \d{4}", r"June \d{4}", r"July \d{4}", r"August \d{4}",
        r"September \d{4}", r"October \d{4}", r"November \d{4}", r"December \d{4}"
    ]

    page = pdf.pages[3]
    text = page.extract_text()

    if text:
        # Search for the specific patterns
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # After finding the pattern, extract the year from the matched string
                year_match = re.search(r"\d{4}", match.group(0))  # Extract the year from the match
                if year_match:
                    year = year_match.group(0)  # This will give the actual year (e.g., '2023')
                    return year

    return None


# Function to extract school code, subject, class, and section from the footer
def extract_info_from_footer(pdf):
  
        # st.write("Calling extract_info_from_footer")  # Debug statement
        for page in pdf.pages:
            # Get the height and width of the page to target the footer area
            page_height = page.height
            page_width = page.width
            
            # Define a box at the bottom of the page to extract footer text
            footer_box = (0, page_height - 50, page_width, page_height)
            footer_text = page.within_bbox(footer_box).extract_text()
            
            if footer_text :
                #st.write("Footer text for info extraction:", footer_text)  # Debug statement
                match = re.search(r"(\d+)/([A-Z]{1,2})(\d{1,2})([A-Z]{1,2})", footer_text.strip())
                #st.write("Match text",match)
                if match:
                    school_code = match.group(1)
                    subject_code = match.group(2)
                    class_value = match.group(3)
                    section = match.group(4)
                    # st.write("Extracted info - School Code:", school_code, "Subject:", subject_code, "Class:", class_value, "Section:", section)  # Debug statement
                    
                    if subject_code == 'E':
                        subject = 'English'
                    elif subject_code == 'M':
                        subject = 'Maths'
                    elif subject_code == 'S':
                        subject = 'Science'
                    elif subject_code == 'C' or subject_code == 'CT':
                        subject = 'Computational Thinking'
                    elif subject_code == 'G':
                        subject = 'Social Studies'
                    elif subject_code == 'H':
                        subject = 'Hindi'    
                    else:
                        subject = 'Unknown'
                    
                    return school_code, subject, class_value, section
        st.write("No school code/subject/class/section found")  # Debug statement
        return None, None, None, None
def search_for_assetdynamic(pdf):
    # Extract text from page 1 (index 0 since indexing starts at 0)
    page = pdf.pages[0]
    page_text = page.extract_text()

    if page_text:
        # Check if 'www.assetdynamic.com' is in the extracted text
        if 'www.assetdynamic.com' in page_text:
            return True
        else:
            return False
    return False    
# Function to extract data from a single PDF
def extract_data_from_pdf(uploaded_file):
    # st.write("Calling extract_data_from_pdf")  # Debug statement
    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        # Extract the year from the PDF
        year = extract_year_from_pdf(pdf)
        if not year:
            st.warning("Year not found in the PDF.")
            return pd.DataFrame()
        
        # Extract school code, subject, class, and section from the footer
        school_code, subject, class_value, section = extract_info_from_footer(pdf)
        if not school_code or not subject or not class_value or not section:
            st.warning("School code, subject, class, or section not found in the PDF footer.")
            return pd.DataFrame()
        
        # Find the page containing "Skill-based Summary"
        page_number = find_skill_summary_page(pdf)
        if page_number is None:
            st.warning("Skill-based Summary not found in the PDF.")
            return pd.DataFrame()
        
        # Extract the table from the identified page
        page = pdf.pages[page_number]
        table = page.extract_table()
    
    # Extract relevant rows and columns
    if table:
        # st.write("Table found in the PDF")  # Debug statement
        data = []
        for row in table[2:]:
            if row[0] is not None and search_for_assetdynamic(pdf) :
                data.append([row[0], row[1], row[2], row[3], row[4]])
            else:
                data.append([row[0], row[1], row[3], row[4], row[5]])
        
        df = pd.DataFrame(data, columns=["S.no", "Skill", "Section Performance", "Class Performance", "National Performance"])
        df['School Code'] = school_code
        df['Subject'] = subject
        df['Class'] = class_value
        df['Section'] = section
        df['Year'] = year  # Add the extracted year here
        
        return df
    else:
        st.warning("No table found in the PDF.")
        return pd.DataFrame()

# Streamlit App
st.title("Skill Based Summary")
st.markdown("This facility is to be able to give you yearwise collection of skills by uploading the TMBs of a school for ASSET Pen and Paper/AD.")

# Upload PDFs
uploaded_files = st.file_uploader("Upload PDF files. Note that you can attach TMBs of as many academic years from 2022 to 2024.", type="pdf", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        df = extract_data_from_pdf(uploaded_file)
        if not df.empty:
            dfs.append(df)
    
    if dfs:
        final_df = pd.concat(dfs, ignore_index=True)

        st.write("Complete Skill list")
        st.dataframe(final_df)
        excel_file_path_complete="Complete Skill Summary.xlsx"
        final_df.to_excel(excel_file_path_complete)

        st.download_button(
            label="Download complete data as Excel File",
            data=open(excel_file_path_complete, "rb").read(),
            file_name="Complete Skill Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Pivot the DataFrame to organize by School Code, Class, Subject, and Year
        pivot_df = final_df.pivot_table(
            index=["School Code", "Class", "Subject", "Skill"],
            columns="Year",
            values=["Class Performance", "National Performance"],
            aggfunc="first"
        ).reset_index()

        # Flatten the multi-level columns
        # pivot_df.columns = [' '.join(col).strip() if col[1] else col[0] for col in pivot_df.columns]

        # Reorder columns to display the Class Performance and National Performance for each year sequentially
        # ordered_columns = (
        #     ["School Code", "Subject", "Skill"] +
        #     [col for year in sorted(final_df['Year'].unique()) for col in [f"Class Performance {year}", f"National Performance {year}"]]
        # )
        # pivot_df = pivot_df[ordered_columns]

        st.write("Skill comparison year wise")
        st.dataframe(pivot_df)


        excel_file_path = "Skill Summary.xlsx"
        pivot_df.to_excel(excel_file_path)

        st.download_button(
            label="Download Pivoted data as Excel File",
            data=open(excel_file_path, "rb").read(),
            file_name="Skill Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No valid tables found in the uploaded PDFs.")  
