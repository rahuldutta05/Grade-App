# components/tables.py

import pandas as pd
import streamlit as st

def display_results_table(calculated_subjects):
    """Renders the final results table for the user."""
    from utils import GRADE_POINTS

    if calculated_subjects:
        result_df = pd.DataFrame(calculated_subjects)
        result_df["Grade Points"] = result_df["Grade"].apply(lambda g: GRADE_POINTS.get(g, 0))
        result_df["Weighted Score"] = result_df["Credits"] * result_df["Grade Points"]
        st.dataframe(result_df, use_container_width=True)