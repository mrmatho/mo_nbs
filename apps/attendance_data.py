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
    csv_f = mo.ui.file(kind="area", label="Attendance CSV file", multiple=False)
    csv_f
    return (csv_f,)


@app.cell
def _(StringIO, csv_f, pd):
    df = pd.DataFrame()
    if csv_f.name():
        byte_content = csv_f.contents()
        decoded_content = byte_content.decode("utf-8")
        df = pd.read_csv(StringIO(decoded_content))
        df["Attendance Tier"] = df["SchlPercentage"].apply(categorize_attendance)


    df
    return (df,)


@app.function
def categorize_attendance(percentage):
    if percentage < 60:
        return "Tier 3"
    elif 60 <= percentage <= 79:
        return "Tier 2"
    else:
        return "Tier 1"


@app.cell
def _(df, mo):
    yr_lvl_dropdown = mo.md("Can't select a Year Level until you have data")
    if len(df) > 0:
        yr_lvl_dropdown = mo.ui.dropdown(
            label="Select Year Level",
            options=df["YearLevel"].dropna().unique().tolist(),
        )
    yr_lvl_dropdown
    return (yr_lvl_dropdown,)


@app.cell
def _(df, px, yr_lvl_dropdown):
    if yr_lvl_dropdown.value:
        yr_df = df[df["YearLevel"] == yr_lvl_dropdown.value]
    else:
        yr_df = df

    if len(yr_df) > 0:
        px.histogram(
            yr_df,
            x="Attendance Tier",
            title="Attendance Tier Distribution",
            color="YearLevel",
        ).show()
    return (yr_df,)


@app.cell
def _(mo, yr_df):
    out = "## Tier 3 Students"
    if len(yr_df) > 0:
        # Tier 3 Student list

        tier_3_students = yr_df[yr_df["Attendance Tier"] == "Tier 3"]
        tier_3_students = tier_3_students[
            [
                "StudentName",
                "YearLevel",
                "TotalInclass",
                "TotalOutClass",
                "SchlPercentage",
            ]
        ]

        # Drop students without a Year level and sort by SchlPercentage
        tier_3_students = tier_3_students.dropna(subset=["YearLevel"]).sort_values(
            by="SchlPercentage"
        )

        # Output mo.md cells for each row in the dataframe
        mo.md("# Tier 3 Students\n\n")
        for index, row in tier_3_students.iterrows():
            out += f"- **{row['StudentName']}** *{row['SchlPercentage']}%*\n"

        out += f"\n\nTotal Tier 3 Students: {len(tier_3_students)}"

        out += f"\n\n## Tier 2 Students"
        tier_2_students = (
            yr_df[yr_df["Attendance Tier"] == "Tier 2"]
            .dropna(subset=["YearLevel"])
            .sort_values(by="SchlPercentage")
        )

        for index, row in tier_2_students.iterrows():
            out += f"- **{row['StudentName']}** *{row['SchlPercentage']}%*\n"
        out += f"\n\nTotal Tier 2 Students: {len(tier_2_students)}"

    mo.md(out)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from io import StringIO

    # < 60, 61 - 79, 80 +
    return StringIO, mo, pd, px


if __name__ == "__main__":
    app.run()
