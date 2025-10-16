# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pandas==2.3.3",
#     "plotly==6.3.1",
# ]
# ///

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="full", auto_download=["html"])


@app.cell
def _(mo):
    mo.md("""#Compass Attendance Tier Analysis""")
    return


@app.cell
def _(mo):
    mo.md(
        """
    The file you need is found in Compass > Whole School (or just a Year Level) > Attendance By Students > Export.

    Don't forget to set the date range you want first!
    """
    )
    return


@app.cell
def _(mo):
    csv_f = mo.ui.file(
        kind="area",
        label="Upload Compass Attendance CSV file here.",
        multiple=False,
    )
    thresholds = mo.md("### Set Attendance Tier Thresholds (or leave as default)")
    lower_thresh = mo.ui.slider(
        label="Tier 3 Threshold",
        start=20,
        stop=80,
        value=60,
        show_value=True,
        include_input=True,
    )
    upper_thresh = mo.ui.slider(
        label="Tier 2 Threshold",
        start=60,
        stop=95,
        value=80,
        show_value=True,
        include_input=True,
    )

    mo.hstack([csv_f, mo.vstack([thresholds, lower_thresh, upper_thresh])])
    return csv_f, lower_thresh, upper_thresh


@app.cell
def _(lower_thresh, mo, upper_thresh):
    mo.md(
        f"""
    **Attendance Threshold set as:**
    - Tier 3: 0% - {lower_thresh.value - 1}%
    - Tier 2: {lower_thresh.value}% - {upper_thresh.value - 1}%
    - Tier 1: {upper_thresh.value}% and above
    """
    )
    return


@app.cell
def _(StringIO, csv_f, lower_thresh, pd, upper_thresh):
    df = pd.DataFrame()
    if csv_f.name():
        byte_content = csv_f.contents()
        decoded_content = byte_content.decode("utf-8")
        df = pd.read_csv(StringIO(decoded_content))

        # Set thresholds from sliders
        thresh_vals = (lower_thresh.value, upper_thresh.value)
        df["Attendance Tier"] = df["SchlPercentage"].apply(
            categorize_attendance, args=(thresh_vals,)
        )
    return (df,)


@app.function
def categorize_attendance(percentage, thresholds):
    if percentage < thresholds[0]:
        return "Tier 3"
    elif thresholds[0] <= percentage < thresholds[1]:
        return "Tier 2"
    else:
        return "Tier 1"


@app.cell
def _(df, mo):
    print(list(df.columns))
    yr_lvl_dropdown = mo.md("Can't select a Year Level until you have data")
    if len(df) > 0:
        if "YearLevel" in df.columns:
            yr_lvl_dropdown = mo.ui.dropdown(
                label="Select Year Level",
                options=df["YearLevel"].dropna().unique().tolist(),
            )
        elif "Form" in df.columns:
            yr_lvl_dropdown = mo.ui.dropdown(
                label="Select Home Group", options=df["Form"]
            )
            df["YearLevel"] = df["Form"]


    mo.vstack([mo.md("## Filter by Year Level or Form"), yr_lvl_dropdown])
    return (yr_lvl_dropdown,)


@app.cell
def _(alt, df, mo, pd, yr_lvl_dropdown):
    yr_df = pd.DataFrame()
    if len(df) > 0 and yr_lvl_dropdown.value:
        yr_df = df[df["YearLevel"] == yr_lvl_dropdown.value].dropna(
            subset=["YearLevel"]
        )
    else:
        yr_df = df
    attendance_tier_chart = None

    if len(yr_df) > 0:
        # Count the number of students in each attendance tier for each year level
        tier_counts = (
            yr_df.groupby(["YearLevel", "Attendance Tier"])
            .size()
            .reset_index(name="Count")
        )

        # Calculate the total number of students per Year Level
        total_counts = yr_df.groupby("YearLevel").size().reset_index(name="Total")

        # Merge the counts with total counts and calculate percentages
        tier_counts = tier_counts.merge(total_counts, on="YearLevel")
        tier_counts["Percentage"] = (
            tier_counts["Count"] / tier_counts["Total"]
        ) * 100

        # Create the Altair chart using percentages
        attendance_tier_chart = (
            alt.Chart(tier_counts)
            .mark_bar()
            .encode(
                x=alt.X("Attendance Tier:N", title="Attendance Tier"),
                y=alt.Y("Percentage:Q", title="Percentage"),
                color="YearLevel:N",
                tooltip=["Attendance Tier", "Count", "Percentage"],
            )
            .properties(title="Attendance Tier Percentage Distribution")
        )

    mo.ui.altair_chart(attendance_tier_chart)
    return (yr_df,)


@app.cell
def _(mo, yr_df):
    out_t3 = "## Tier 3 Students"

    out_t2 = "\n\n## Tier 2 Students"
    if len(yr_df) > 0:
        # Tier 3 Student list

        tier_3_students = yr_df[yr_df["Attendance Tier"] == "Tier 3"]

        # Drop students without a Year level and sort by SchlPercentage
        tier_3_students = tier_3_students.dropna(subset=["YearLevel"]).sort_values(
            by="SchlPercentage"
        )

        # Output mo.md cells for each row in the dataframe

        for index, row in tier_3_students.iterrows():
            out_t3 += f"\n- **{row['StudentName']}** *{row['SchlPercentage']}%*"

        out_t3 += f"\n\nTotal Tier 3 Students: {len(tier_3_students)}"

        tier_2_students = (
            yr_df[yr_df["Attendance Tier"] == "Tier 2"]
            .dropna(subset=["YearLevel"])
            .sort_values(by="SchlPercentage")
        )

        for index, row in tier_2_students.iterrows():
            out_t2 += f"\n- **{row['StudentName']}** *{row['SchlPercentage']}%*"
        out_t2 += f"\n\nTotal Tier 2 Students: {len(tier_2_students)}"

    mo.hstack([mo.md(out_t3), mo.md(out_t2)])
    return tier_2_students, tier_3_students


@app.cell
def _(mo, tier_2_students, tier_3_students, yr_df):
    data_frames_out = ""
    if len(yr_df) > 0:
        data_frames_out = mo.vstack(
            [
                mo.md("## Tier 3 Students (All Data)"),
                tier_3_students,
                mo.md("## Tier 2 Students (All Data)"),
                tier_2_students,
                mo.md("## Full Data Table (with Tier lists)"),
                yr_df,
            ]
        )

    data_frames_out
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from io import StringIO
    return StringIO, alt, mo, pd


if __name__ == "__main__":
    app.run()
