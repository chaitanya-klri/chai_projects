import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO

# Streamlit app title
st.title("Concept Level Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type="xlsx")

if uploaded_file is not None:

    

    
    # Read the data from the uploaded file
    sheet_name_trail = 'result'
    copy_trail_df = pd.read_excel(uploaded_file, sheet_name=sheet_name_trail)
    
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
    concepts_df = pd.DataFrame(list(concept_levels.items()), columns=['Cluster', 'Concept Level'])

    # Merge the user-provided concept levels back into the main DataFrame
    merged_df = pd.merge(copy_trail_df, concepts_df, on='Cluster', how='left')

    # Sort the DataFrame by Question_Number to ensure a continuous line
    merged_df = merged_df.sort_values(by='Question_Number')

    # Extract unique question numbers and corresponding concept levels and modes
    question_numbers = merged_df['Question_Number'].values
    concept_levels = merged_df['Concept Level'].values
    modes = merged_df['Mode'].values

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title('Concept Level Analysis')
    ax.set_xlabel('Question Number')
    ax.set_ylabel('Concept Level')
    ax.yaxis.get_major_locator().set_params(integer=True)

    # Plot a smooth line for concept levels and change color segments based on mode
    for i in range(1, len(question_numbers)):
        color = 'green' if modes[i] == 'Learn' else 'red' if modes[i] == 'Remediation' else 'blue'
        ax.plot(question_numbers[i-1:i+1], concept_levels[i-1:i+1], color=color, linestyle='-')

        # For "Challenge" mode, add markers
        if modes[i] == 'Challenge':
            ax.scatter(question_numbers[i], concept_levels[i], color='blue', marker='^', s=100, label='Challenge' if i == 1 else "")

    # Adding legend manually for the other modes since only Challenge has markers
    ax.plot([], [], color='green', label='Learn')
    ax.plot([], [], color='red', label='Remediation')

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
        correctness = merged_df[(merged_df['Cluster'] == cluster) & (merged_df['Mode'] == current_mode)]['Correctness'].values

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
            # Update the previous mode and accuracy
            table_data[-1]['Accuracy'] = round((table_data[-1]['Accuracy'] + correctness.sum() / len(correctness)) / 2, 2)

        # Update the previous mode
        previous_mode = current_mode

    # Finalize the last row's end question number and number of questions
    if table_data:
        table_data[-1]['End Question Number'] = merged_df.iloc[-1]['Question_Number']
        table_data[-1]['Number of Questions'] = table_data[-1]['End Question Number'] - table_data[-1]['Start Question Number'] + 1

    # Convert the list to a DataFrame and display it
    table_df = pd.DataFrame(table_data)
    st.write("Progressive Table of Clusters, Concept Levels, Modes, Number of Questions, Accuracy, Start and End Question Numbers")
    st.dataframe(table_df)

    # Option to download the table as a CSV file
    csv = table_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Table as CSV",
        data=csv,
        file_name="concept_level_table.csv",
        mime="text/csv"
    )
