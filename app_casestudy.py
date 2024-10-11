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
    sheet_name_trail = 'Copy student trail here'
    copy_trail_df = pd.read_excel(uploaded_file, sheet_name=sheet_name_trail)
    
    # Extract unique concepts
    unique_concepts = copy_trail_df['Cluster'].unique()

    # Dictionary to store user inputs for concept levels
    concept_levels = {}

    st.write("Enter the levels for the following concepts:")
    for concept in unique_concepts:
        # Get user input for each concept level
        level = st.number_input(f"Level for '{concept}':", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
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

    # Step 4: Build the progressive table
    table_data = []
    for mode in merged_df['Mode'].unique():
        mode_df = merged_df[merged_df['Mode'] == mode]
        for cluster in mode_df['Cluster'].unique():
            cluster_df = mode_df[mode_df['Cluster'] == cluster]
            concept_level = cluster_df['Concept Level'].iloc[0]
            num_questions = len(cluster_df)
            correctness = cluster_df['Correctness'].values
            accuracy = correctness.sum() / len(correctness) if len(correctness) > 0 else 0

            table_data.append({
                'Cluster': cluster,
                'Concept Level': concept_level,
                'Mode': mode,
                'Number of Questions': num_questions,
                'Accuracy': round(accuracy, 2)
            })

    # Convert the list to a DataFrame and display it
    table_df = pd.DataFrame(table_data)
    st.write("Progressive Table of Clusters, Concept Levels, Modes, Number of Questions, and Accuracy")
    st.dataframe(table_df)

    # Option to download the table as a CSV file
    csv = table_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Table as CSV",
        data=csv,
        file_name="concept_level_table.csv",
        mime="text/csv"
    )
