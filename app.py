import streamlit as st
import pdfplumber
import pandas as pd
import os

def extract_subject_class(filename):
    # Split the filename and extract the relevant part
    parts = filename.split('_')
    subject_code = parts[1][0]
    class_code = int(parts[1][1:2])
    section_code = parts[1][2]

    if class_code == 1:
        class_code = 10

    # Map the subject code to the full name
    subject_mapping = {'E': 'English', 'M': 'Maths', 'S': 'Science'}
    subject = subject_mapping.get(subject_code, 'Unknown')

    return subject, class_code, section_code

def process_pdfs(uploaded_files):
    all_dataframes = []

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        # Extract subject and class from the filename
        subject, class_code, section_code = extract_subject_class(filename)

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
            label="Download Combined Data as Excel",
            data=open(excel_file_path, "rb").read(),
            file_name="combined_data.xlsx",
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

        # Group data by class and subject, calculate the counts in each range
        ranges = ['91-100', '81-90', '71-80', '61-70', '51-60', '<50']
        range_bins = [0, 51, 61, 71, 81, 91, 100]

        range_counts_per_class = final_df.groupby(['Class', 'Subject'])['Percentile'].apply(
            lambda x: pd.cut(x, bins=range_bins, labels=ranges).value_counts().sort_index()).unstack().fillna(0)
        
        # range_counts_per_class = final_df.groupby(['Class', 'Subject'])['Percentile']

        range_counts_per_class = range_counts_per_class.astype(int)

        st.write("Class and Subject-wise Percentile Distribution:")
        st.write(range_counts_per_class)

        # Save the range data to Excel
        excel_file_path_school = 'ranges_school.xlsx'
        excel_file_path_class = 'ranges_class.xlsx'
        
        range_df.to_excel(excel_file_path_school, index=False)
        range_counts_per_class.to_excel(excel_file_path_class)

        st.download_button(
            label="Download School-wise Ranges as Excel",
            data=open(excel_file_path_school, "rb").read(),
            file_name="ranges_school.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="Download Class-wise Ranges as Excel",
            data=open(excel_file_path_class, "rb").read(),
            file_name="ranges_class.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
