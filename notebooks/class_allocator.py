import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from class_allocation import (
        load_data,
        build_friendship_graph,
        allocate_groups,
        validate_groups
    )
    return (
        allocate_groups,
        build_friendship_graph,
        load_data,
        mo,
        pd,
        validate_groups,
    )


@app.cell
def _(mo):
    mo.md(
        """
    # Student Group Allocation System

    This system allocates students into balanced groups while trying to ensure 
    each student has at least one friend in their group.

    **Priority Order:**
    1. Equal group sizes (±1 student variance)
    2. At least 1 friend per student (best effort)
    """
    )
    return


@app.cell
def _(mo):
    # File upload control
    file_upload = mo.ui.file(
        filetypes=[".csv", ".xlsx", ".xls"],
        multiple=False,
        label="Upload Student Data File"
    )

    mo.md(f"""
    ## 1. Upload Student Data

    Upload a CSV or Excel file with the following columns:
    - Student Name
    - Friend 1
    - Friend 2
    - Friend 3
    - Friend 4

    {file_upload}
    """)
    return (file_upload,)


@app.cell
def _(mo):
    # Similarity threshold slider
    similarity_slider = mo.ui.slider(
        start=50,
        stop=100,
        step=5,
        value=85,
        label="Fuzzy Matching Threshold (%)",
        show_value=True
    )

    # Number of groups slider
    num_groups_slider = mo.ui.slider(
        start=2,
        stop=12,
        step=1,
        value=6,
        label="Number of Groups",
        show_value=True
    )

    mo.md(f"""
    ## 2. Configure Settings

    **Fuzzy Matching Threshold**: How similar must friend names be to match with student names?
    - Higher = stricter matching (fewer false matches, might miss typos)
    - Lower = more lenient (catches more typos, might have false matches)

    {similarity_slider}

    **Number of Groups**: How many groups should students be divided into?

    {num_groups_slider}
    """)
    return num_groups_slider, similarity_slider


@app.cell
def _(file_upload, load_data, mo):
    # Load the data when file is uploaded
    if file_upload.value:
        try:
            # Save uploaded file temporarily
            import tempfile
            import os

            suffix = os.path.splitext(file_upload.name())[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_upload.contents())
                tmp_path = tmp.name

            df = load_data(tmp_path)

            # Clean up temp file
            os.unlink(tmp_path)

            data_loaded = True
            load_message = mo.md(f"✅ **Loaded {len(df)} students successfully!**")
        except Exception as e:
            df = None
            data_loaded = False
            load_message = mo.md(f"❌ **Error loading file:** {str(e)}")
    else:
        df = None
        data_loaded = False
        load_message = mo.md("⏳ *Waiting for file upload...*")

    load_message
    return data_loaded, df


@app.cell
def _(data_loaded, df, mo):
    # Display student data preview
    if data_loaded and df is not None:
        mo.md(f"""
        ## 3. Data Preview

        **Total Students:** {len(df)}

        Here's a preview of your data:
        """)
    return


@app.cell
def _(data_loaded, df, mo):
    # Show data table
    if data_loaded and df is not None:
        df_show = mo.ui.data_editor(df)
    df_show
    return


@app.cell
def _(build_friendship_graph, data_loaded, df, mo, similarity_slider):
    # Build friendship graph and show matching results
    if data_loaded and df is not None:
        threshold = similarity_slider.value
        friendship_graph = build_friendship_graph(df, threshold=threshold)

        # Calculate some stats
        total_friendships = sum(len(friends) for friends in friendship_graph.values())
        students_with_friends = sum(1 for friends in friendship_graph.values() if len(friends) > 0)
        students_without_friends = len(df) - students_with_friends

        mo.md(f"""
        ## 4. Friendship Matching Results

        Using threshold of **{threshold}%** similarity:

        - **Total friendship connections found:** {total_friendships}
        - **Students with at least 1 friend match:** {students_with_friends}
        - **Students with no friend matches:** {students_without_friends}
        """)
    else:
        friendship_graph = None

    friendship_graph
    return (friendship_graph,)


@app.cell
def _(data_loaded, friendship_graph, mo, pd):
    # Show friendship details
    if data_loaded and friendship_graph is not None:
        # Create a summary table
        friendship_summary = []
        for student, friends in friendship_graph.items():
            friendship_summary.append({
                'Student': student,
                'Number of Friends': len(friends),
                'Friends': ', '.join(friends) if friends else 'None'
            })

        friendship_df = pd.DataFrame(friendship_summary)
        friendship_df = friendship_df.sort_values('Number of Friends', ascending=False)

        _out = mo.hstack([mo.md("### Friendship Details"), friendship_df])

    _out
    return (friendship_df,)


@app.cell
def _(data_loaded, friendship_df):
    if data_loaded and friendship_df is not None:
        friendship_df
    friendship_df
    return


@app.cell
def _(
    allocate_groups,
    data_loaded,
    df,
    friendship_graph,
    mo,
    num_groups_slider,
):
    # Allocate groups
    if data_loaded and df is not None and friendship_graph is not None:
        num_groups = num_groups_slider.value
        groups = allocate_groups(df, friendship_graph, num_groups=num_groups)

        _out = mo.md(f"""
        ## 5. Group Allocation

        Students have been allocated into **{num_groups} groups**.
        """)
    else:
        groups = None
        num_groups = 6
        _out = "Meh"

    _out
    return (groups,)


@app.cell
def _(data_loaded, friendship_graph, groups, mo, validate_groups):
    # Validate and show results
    if data_loaded and groups is not None and friendship_graph is not None:
        validation = validate_groups(groups, friendship_graph)

        _out = mo.md(f"""
        ## 6. Validation Results

        ### Group Size Balance
        - **Group sizes:** {validation['group_sizes']}
        - **Min size:** {validation['min_group_size']} | **Max size:** {validation['max_group_size']} | **Variance:** {validation['group_size_variance']}

        ### Friend Satisfaction
        - **Satisfaction rate:** {validation['satisfaction_rate']}% (students with ≥1 friend in their group)
        - **Average friends per student in group:** {validation['average_friends_per_student']}

        ### Distribution of Friends per Student
        - **0 friends:** {validation['students_with_friends'][0]} students
        - **1 friend:** {validation['students_with_friends'][1]} students
        - **2 friends:** {validation['students_with_friends'][2]} students
        - **3 friends:** {validation['students_with_friends'][3]} students
        - **4+ friends:** {validation['students_with_friends'][4]} students
        """)
    else:
        validation = None
        _out = "meh"
    _out
    return (validation,)


@app.cell
def _(data_loaded, groups, mo):
    # Show groups in detail
    _out = ""
    if data_loaded and groups is not None:
        _out = mo.md("### Detailed Group Assignments")
    _out
    return


@app.cell
def _(data_loaded, friendship_graph, groups, pd):
    # Create detailed group display
    if data_loaded and groups is not None and friendship_graph is not None:
        group_details = []

        for idx, group in enumerate(groups, 1):
            for _student in group:
                _friends = friendship_graph.get(_student, [])
                friends_in_group = [f for f in _friends if f in group]

                group_details.append({
                    'Group': idx,
                    'Student': _student,
                    'Friends in Group': len(friends_in_group),
                    'Friend Names': ', '.join(friends_in_group) if friends_in_group else 'None'
                })

        groups_df = pd.DataFrame(group_details)
    groups_df
    return (groups_df,)


@app.cell
def _(data_loaded, mo, validation):
    # Show students with no friends
    if data_loaded and validation is not None and validation['students_with_0_friends'] > 0:
        mo.md(f"""
        ### ⚠️ Students Without Friends in Their Group

        The following **{validation['students_with_0_friends']} students** do not have any of their listed friends in their group:

        {', '.join(validation['students_without_friends_list'])}
        """)
    return


@app.cell
def _(data_loaded, groups_df, mo):
    # Export option
    if data_loaded and groups_df is not None:
        _out = mo.md("""
        ## 7. Export Results

        You can download the group assignments as a CSV file by copying the table above
        or using the download functionality in your marimo notebook.
        """)

    _out
    return


if __name__ == "__main__":
    app.run()
