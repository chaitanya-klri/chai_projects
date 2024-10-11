import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO

# Streamlit app title
st.title("Learning Journey of Students")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type="xlsx")

if uploaded_file is not None:
    # Prompt for the student's name
    student_name = st.text_input("Enter the student's name:")

    # Read the data from the uploaded file
    sheet_name_trail = 'result'
    copy_trail_df = pd.read_excel(uploaded_file, sheet_name=sheet_name_trail)
    
    # Extract unique topics and set the first one as the default topic for the chart
    topics = copy_trail_df['Topic'].unique()
    topic = topics[0] if len(topics) > 0 else "Topic"

    # Extract unique concepts
    unique_concepts = copy_trail_df['Cluster'].unique()

    # Dictionary to store user inputs for concept levels
    concept_levels = {}

    st.write("Enter the levels for the following concepts:")
    for concept in unique_concepts:
        # Get user input for each concept level (integer values only)
        level = st.number_input(f"Level for '{concept}':", min_value=-1000, max_value=1000, value=0, step=1, format="%d")
        concept_levels[concept] = level

    # Convert the dictionary to a DataFrame
    concepts_df = pd.DataFrame(list(concept_levels.items()), columns=['Concept', 'Concept Level'])

    # Display the table of concepts and levels entered by the user
    st.write("Concept Levels Entered by User:")
    st.dataframe(concepts_df)

    # Save the concepts DataFrame as an Excel file in a BytesIO object
    concepts_excel_buf = BytesIO()
    with pd.ExcelWriter(concepts_excel_buf, engine='openpyxl') as writer:
        concepts_df.to_excel(writer, index=False, sheet_name='Concept Levels')
    concepts_excel_buf.seek(0)

    # Provide a download button for the Concept Levels Excel file
    st.download_button(
        label="Download Concept Levels as Excel",
        data=concepts_excel_buf,
        file_name="concept_levels.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Merge the user-provided concept levels back into the main DataFrame
    merged_df = pd.merge(copy_trail_df, concepts_df, left_on='Cluster', right_on='Concept', how='left')

    # Sort the DataFrame by Question_Number to ensure a continuous line
    merged_df = merged_df.sort_values(by='Question_Number')

    # Extract unique question numbers and corresponding concept levels and modes
    question_numbers = merged_df['Question_Number'].values
    concept_levels = merged_df['Concept Level'].values
    modes = merged_df['Mode'].values

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    if student_name:
        chart_title = f"Learning trail of {student_name} - {topic}"
    else:
        chart_title = f"Learning trail - {topic}"
    ax.set_title(chart_title)
    ax.set_xlabel('Question Number')
    ax.set_ylabel('Concept Level')
    ax.yaxis.get_major_locator().set_params(integer=True)

    # Set the x-axis limits based on the question number range
    ax.set_xlim([question_numbers.min(), question_numbers.max()])

    # Extend the y-axis limits based on the concept levels (adding padding) and set the major unit to 1
    ax.set_ylim([concept_levels.min() - 1, concept_levels.max() + 1])
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))

    # Plot a smooth line for concept levels and change color segments based on mode
    for i in range(1, len(question_numbers)):
        color = 'green' if modes[i] == 'Learn' else 'red' if modes[i] == 'Remediation' else 'blue'
        ax.plot(question_numbers[i-1:i+1], concept_levels[i-1:i+1], color=color, linestyle='-')

        # For "Challenge" mode, add markers
        if modes[i] == 'Challenge':
            ax.scatter(question_numbers[i], concept_levels[i], color='blue', marker='^', s=100)

    # Adding legend manually for all modes
    ax.plot([], [], color='green', label='Learn')
    ax.plot([], [], color='red', label='Remediation')
    ax.scatter([], [], color='blue', marker='^', s=100, label='Challenge')

    ax.legend()
    st.pyplot(fig)

    # Save the figure to a BytesIO object for download
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    # Provide a download button for the figure
    st.download_button(
        label="Download Plot",
        data=buf,
        file_name="concept_level_analysis.png",
        mime="image/png"
    )

    # Step 4: Build the progressive table with start and end question numbers
    table_data = []
    previous_mode = None
    start_question_number = None

    for i, (index, row) in enumerate(merged_df.iterrows()):
        current_mode = row['Mode']
        current_question_number = row['Question_Number']
        cluster = row['Cluster']
        concept_level = row['Concept Level']

        # Dynamically filter the correctness values for this row
        correctness = merged_df[(merged_df['Cluster'] == cluster) & (merged_df['Mode'] == current_mode) & (merged_df['Question_Number'] == current_question_number)]['Correctness'].values

        if previous_mode is None or current_mode != previous_mode:
            # New mode detected or first entry
            if start_question_number is not None:
                # If this is not the first entry, finalize the previous row
                table_data[-1]['End Question Number'] = merged_df.iloc[i-1]['Question_Number']
                table_data[-1]['Number of Questions'] = table_data[-1]['End Question Number'] - table_data[-1]['Start Question Number'] + 1

            # Set the start question number for the new mode
            start_question_number = current_question_number

            # Add a new row for the new mode
            table_data.append({
                'Cluster': cluster,
                'Concept Level': concept_level,
                'Mode': current_mode,
                'Number of Questions': 0,  # Will be filled later
                'Accuracy': round(correctness.sum() / len(correctness), 2) if len(correctness) > 0 else 0,
                'Start Question Number': start_question_number,
                'End Question Number': None  # To be filled in the next iteration
            })
        else:
            # Update the previous mode and accuracy dynamically
            table_data[-1]['Concept Level'] = concept_level
            if len(correctness) > 0:
                table_data[-1]['Accuracy'] = round((table_data[-1]['Accuracy'] + correctness.sum()) / 2, 2)

        # Update the previous mode
        previous_mode = current_mode

    # Finalize the last row's end question number and number of questions
    if table_data:
        table_data[-1]['End Question Number'] = merged_df.iloc[-1]['Question_Number']
        table_data[-1]['Number of Questions'] = table_data[-1]['End Question Number'] - table_data[-1]['Start Question Number'] + 1

    # Convert the list to a DataFrame
    table_df = pd.DataFrame(table_data)

    # Save the DataFrame as an Excel file in a BytesIO object
    excel_buf = BytesIO()
    with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
        table_df.to_excel(writer, index=False, sheet_name='Concept Level Table')
    excel_buf.seek(0)

    st.write(table_df)
    # Provide a download button for the Excel file
    st.download_button(
        label="Download Table as Excel",
        data=excel_buf,
        file_name="concept_level_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
