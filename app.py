import streamlit as st
import pdfplumber
import pandas as pd
import os

def extract_subject_class(filename):
    # Split the filename and extract the relevant part
    parts = filename.split('_')
    school_code=parts[0]
    subject_code = parts[1][0]
    class_code = int(parts[1][1:2])
    section_code = parts[1][2]

    if class_code == 1:
        class_code = 10

    # Map the subject code to the full name
    subject_mapping = {'E': 'English', 'M': 'Maths', 'S': 'Science'}
    subject = subject_mapping.get(subject_code, 'Unknown')

    return school_code,subject, class_code, section_code

def process_pdfs(uploaded_files):
    all_dataframes = []

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        # Extract subject and class from the filename
        school_code,subject, class_code, section_code = extract_subject_class(filename)

        with pdfplumber.open(uploaded_file) as pdf:
            try:
                # Access page 3 (index 2 since it's 0-based)
                page = pdf.pages[2]
                # Extract the table from the page
                tables = page.extract_tables()

                # Check if any tables are found
                if tables:
                    table = tables[0]

                    # Create lists to hold student names and percentiles
                    students = []
                    percentiles = []

                    # Iterate over the rows starting from the second row (skipping the header)
                    for row in table[1:]:
                        student_name = row[1]  # Student name is in the second column
                        percentile = row[-2]  # Percentile is the second last column

                        # Append to respective lists
                        students.append(student_name)
                        percentiles.append(percentile)

                    # Create a DataFrame for this PDF
                    df = pd.DataFrame({
                        'School Code' : school_code,
                        'Student': students,
                        'Percentile': percentiles,
                        'Subject': subject,
                        'Class': class_code,
                        'Section': section_code
                    })
                    df['Percentile'] = pd.to_numeric(df['Percentile'], errors='coerce')
                    df = df.drop(index=0).reset_index(drop=True)

                    # Append the DataFrame to the list
                    all_dataframes.append(df)
            except IndexError:
                st.warning(f"Page 3 not found in {filename}, skipping this file.")

    # Concatenate all DataFrames into one
    if all_dataframes:
        final_df = pd.concat(all_dataframes, ignore_index=True)
        return final_df
    else:
        st.warning("No valid data extracted from the PDFs.")
        return None

# Streamlit app
st.title("PDF Student Performance Analyzer")
st.markdown("Upload the TMB's of one academic year. Use this to get the percentile score distribution for an academic year. ")


# File uploader
uploaded_files = st.file_uploader("Upload PDFs", accept_multiple_files=True, type=["pdf"])

if uploaded_files:
    final_df = process_pdfs(uploaded_files)
    
    if final_df is not None:
        st.write("Data Overview:")
        st.write(final_df)

        # Drop NaN values in Percentile for analysis
        final_df = final_df.dropna(subset=['Percentile'])

        # Save to Excel
        excel_file_path = 'combined_data.xlsx'
        final_df.to_excel(excel_file_path, index=False)

        st.download_button(
            label="Download Student Wise Percentile scores as Excel",
            data=open(excel_file_path, "rb").read(),
            file_name="Student Wise Percentile scores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Defining percentile ranges and counting the number of students in each range
        ranges = {
            '91-100': final_df[(final_df['Percentile'] >= 91) & (final_df['Percentile'] <= 100)].shape[0],
            '81-90': final_df[(final_df['Percentile'] >= 81) & (final_df['Percentile'] <= 90)].shape[0],
            '71-80': final_df[(final_df['Percentile'] >= 71) & (final_df['Percentile'] <= 80)].shape[0],
            '61-70': final_df[(final_df['Percentile'] >= 61) & (final_df['Percentile'] <= 70)].shape[0],
            '51-60': final_df[(final_df['Percentile'] >= 51) & (final_df['Percentile'] <= 60)].shape[0],
            'Less than 50': final_df[final_df['Percentile'] <= 50].shape[0]
        }

        # Creating a DataFrame to display the ranges and their respective counts
        range_df = pd.DataFrame(list(ranges.items()), columns=['Percentile Range', 'Number of Students'])


   # Create a function to categorize percentiles into ranges
        def categorize_percentile(percentile):
            if percentile < 50:
                return '<50 Percentile'
            elif 51 <= percentile <= 60:
                return '51-60 Percentile'
            elif 61 <= percentile <= 70:
                return '61-70 Percentile'
            elif 71 <= percentile <= 80:
                return '71-80 Percentile'
            elif 81 <= percentile <= 90:
                return '81-90 Percentile'
            else:
                return '91-100 Percentile'

        # Apply the categorization function to create a new column
        final_df['Percentile Range'] = final_df['Percentile'].apply(categorize_percentile)

        # Create a pivot table
        pivot_table = pd.pivot_table(final_df, 
                                       index=['Class', 'Subject'], 
                                       columns='Percentile Range', 
                                       values='Student', 
                                       aggfunc='count', 
                                       fill_value=0)

        # Reset index to flatten the DataFrame for better readability
        pivot_table = pivot_table.reset_index()

        st.write("Class and Subject-wise Percentile Distribution:")
        st.markdown("The output will be number of students in various percentile score ranges.")
        st.write(pivot_table)

        # Save the pivot table to Excel
        excel_file_path = 'pivot_table_class_subject.xlsx'
        pivot_table.to_excel(excel_file_path, index=False)

        

        st.download_button(
            label="Download Class and Subject-wise Percentile Distribution as Excel",
            data=open(excel_file_path, "rb").read(),
            file_name="pivot_table_class_subject.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        

        # Save the range data to Excel
        excel_file_path_school = 'ranges_school.xlsx'
        excel_file_path_class = 'ranges_class.xlsx'
        
        range_df.to_excel(excel_file_path_school, index=False)

        st.write("Full School Percentile distribution for all subjects:")
        st.write(range_df)

        st.download_button(
            label="Download Full School Percentile distribution as Excel",
            data=open(excel_file_path_school, "rb").read(),
            file_name="School Percentile distribution.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

