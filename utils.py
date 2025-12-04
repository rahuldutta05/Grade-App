import pandas as pd
import streamlit as st
import os

# Define grade points mapping
GRADE_POINTS = {"S": 10, "A": 9, "B": 8, "C": 7, "D": 6, "E": 5, "F": 0}

def get_course_data(file_path):
    """
    Loads and returns the course DataFrame from a specified file path.
    """
    try:
        if not os.path.exists(file_path):
            st.error(f"Error: The file '{file_path}' was not found.")
            st.stop()
        
        courses_df = pd.read_csv(file_path, encoding="latin1")
        courses_df.columns = courses_df.columns.str.strip()
        courses_df["Display"] = courses_df["Course Code"].astype(str) + " - " + courses_df["Course Name"]
        return courses_df
    except Exception as e:
        st.error(f"An error occurred while loading the course data: {e}")
        st.stop()
        return None

def get_paired_course(course_code, courses_df):
    """
    Finds the paired theory/lab course based on the course code.
    Looks for a 'P' (Practical/Lab) or 'L' (Theory/Lecture) suffix.
    """
    last_char = course_code[-1].upper()
    if last_char == 'L':
        paired_code = course_code[:-1] + 'P'
    elif last_char == 'P':
        paired_code = course_code[:-1] + 'L'
    else:
        return None

    paired_course_row = courses_df[courses_df["Course Code"] == paired_code]
    if not paired_course_row.empty:
        return paired_course_row.iloc[0]
    return None

def calculate_gpa(subjects):
    """
    Calculates the GPA based on a list of subjects, their credits, and grades.
    Non-graded courses are excluded from GPA calculation.
    """
    total_grade_points = 0
    total_credits = 0
    
    for subject in subjects:
        # Check if the course is non-graded and handle accordingly
        if "Non-Graded Core Requirement" in subject.get("Type", ""):
            # Non-graded courses do not contribute to GPA
            continue
        
        grade = subject["Grade"]
        credits = subject["Credits"]
        
        if grade in GRADE_POINTS:
            grade_point = GRADE_POINTS[grade]
            total_grade_points += grade_point * credits
            total_credits += credits
        
    if total_credits == 0:
        return 0.0, 0.0
    
    gpa = total_grade_points / total_credits
    return gpa, total_credits