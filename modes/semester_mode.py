import streamlit as st
import pandas as pd
from utils import get_paired_course, calculate_gpa, GRADE_POINTS
from components.tables import display_results_table

MAX_CREDITS = 30.5
GRADE_OPTIONS = list(GRADE_POINTS.keys())
NON_GRADED_OPTIONS = ["P", "F"]

def on_course_change(row_id):
    """
    Callback to handle changes to the course selectbox.
    Updates the session state and checks for paired courses to add.
    """
    selected_course_display = st.session_state[f"course_select_{row_id}"]
    courses_df = st.session_state.courses_df
    for row in st.session_state.rows:
        if row["id"] == row_id:
            row["course_display"] = selected_course_display
        
            if selected_course_display:
                selected_df = courses_df[courses_df["Display"] == selected_course_display].iloc[0]
                is_non_graded = "Non-Graded Core Requirement" in selected_df["Type"]
                
                if is_non_graded and row.get("grade") not in NON_GRADED_OPTIONS:
                    row["grade"] = "P"
                elif not is_non_graded and row.get("grade") not in GRADE_OPTIONS:
                    row["grade"] = "S"
            else:
                row["grade"] = "S"
            break
            
    if selected_course_display:
        selected_df = courses_df[courses_df["Display"] == selected_course_display].iloc[0]
        course_code = selected_df["Course Code"]
        
        paired_course_row = get_paired_course(course_code, courses_df)
        
        paired_exists = False
        if paired_course_row is not None:
            for existing_row in st.session_state.rows:
                if existing_row["course_display"] == paired_course_row["Display"]:
                    paired_exists = True
                    break
        
        if paired_course_row is not None and not paired_exists:
            idx = next(i for i, r in enumerate(st.session_state.rows) if r["id"] == row_id)
            new_row = {
                "id": st.session_state.next_id,
                "course_display": paired_course_row["Display"],
                "grade": "P" if "Non-Graded Core Requirement" in paired_course_row["Type"] else "S"
            }
            st.session_state.rows.insert(idx + 1, new_row)
            st.session_state.next_id += 1

def add_new_row(idx):
    """Callback to add a new row at a specific index."""
    new_row = {"id": st.session_state.next_id, "course_display": None, "grade": "S"}
    st.session_state.rows.insert(idx + 1, new_row)
    st.session_state.next_id += 1
    
def delete_row(row_id):
    """Callback to delete a row by its unique ID."""
    if len(st.session_state.rows) > 1:
        st.session_state.rows = [row for row in st.session_state.rows if row["id"] != row_id]

def run(courses_df):
    """Main function for the Semester Mode UI."""
    st.session_state.courses_df = courses_df
    semester_number = st.number_input("Semester Number", min_value=1, max_value=8, value=1, step=1)
    st.subheader(f"Semester {semester_number} Courses")
    
    if "rows" not in st.session_state:
        st.session_state.rows = [{"id": 0, "course_display": None, "grade": "S"}]
        st.session_state.next_id = 1
        
    calculated_subjects = []
    selected_courses_list = [row["course_display"] for row in st.session_state.rows if row["course_display"] is not None]
    header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([0.5, 3, 2, 1, 1, 0.5])
    with header_col1:
        st.write("")
    with header_col2:
        st.markdown("**Course**")
    with header_col3:
        st.markdown("**Type**")
    with header_col4:
        st.markdown("**Credits**")
    with header_col5:
        st.markdown("**Grade**")
    with header_col6:
        st.write("")

    for idx, row in enumerate(st.session_state.rows):
        row_id = row["id"]
        add_col, course_col, type_col, credits_col, grade_col, del_col = st.columns([0.5, 3, 2, 1, 1, 0.5])

        with add_col:
            st.button("➕", key=f"add_{row_id}", on_click=add_new_row, args=(idx,))
        
        with course_col:
            current_course = row["course_display"]
            available_courses = sorted(courses_df["Display"].tolist())
            available_options = [c for c in available_courses if c not in selected_courses_list or c == current_course]
            initial_index = available_options.index(current_course) if current_course in available_options else None
            
            st.selectbox(
                label="Select a course...",
                options=available_options,
                index=initial_index,
                key=f"course_select_{row_id}",
                on_change=on_course_change,
                args=(row_id,),
                placeholder="Search for a course...",
                label_visibility="collapsed"
            )

        course_info = {}
        is_non_graded = False
        if row["course_display"] is not None:
            selected_df = courses_df[courses_df["Display"] == row["course_display"]].iloc[0]
            
            course_info["type"] = selected_df["Type"].strip()
            course_info["credits"] = float(selected_df["Credits"])
            is_non_graded = "Non-Graded Core Requirement" in course_info["type"]
        else:
            course_info["type"] = ""
            course_info["credits"] = 0.0
            
        with type_col:
            st.text_input(f"", value=course_info["type"], key=f"type_{row_id}", disabled=True, label_visibility="collapsed")
        with credits_col:
            st.number_input(f"", value=course_info["credits"], key=f"credits_{row_id}", disabled=True, format="%.2f", label_visibility="collapsed")
        with grade_col:
            if is_non_graded:
                grade_options = NON_GRADED_OPTIONS
            else:
                grade_options = GRADE_OPTIONS
            
            current_grade = row.get("grade")
            if current_grade not in grade_options:
                current_grade = grade_options[0]
                row["grade"] = current_grade

            grade = st.selectbox(
                f"",
                options=grade_options,
                index=grade_options.index(current_grade),
                key=f"grade_{row_id}",
                label_visibility="collapsed"
            )
            row["grade"] = grade

        with del_col:
            st.button("➖", key=f"del_{row_id}", on_click=delete_row, args=(row_id,))
        
        if row["course_display"] is not None:
            calculated_subjects.append({
                "Course": row["course_display"],
                "Type": course_info["type"],
                "Credits": course_info["credits"],
                "Grade": grade,
            })
    if calculated_subjects:
        st.markdown("---")
        st.subheader("Results")
        
        graded_subjects = [
            sub for sub in calculated_subjects
            if "Non-Graded Core Requirement" not in sub["Type"]
        ]
        
        total_credits = sum(sub["Credits"] for sub in calculated_subjects)
        
        gpa, gpa_credits = calculate_gpa(graded_subjects)

        has_non_graded_course = any("Non-Graded Core Requirement" in sub["Type"] for sub in calculated_subjects)

        if has_non_graded_course:
            st.info(f"📚 **Total Credits:** {total_credits:.2f} (Credits from all courses)")
            st.info(f"📚 **GPA Credits:** {gpa_credits:.2f} (Credits used for GPA calculation)")
        else:
            st.info(f"📚 **Total Credits:** {total_credits:.2f}")

        if total_credits > MAX_CREDITS:
            st.warning(f"⚠️ **Total credits ({total_credits}) exceed the maximum limit of {MAX_CREDITS}.** Please remove some courses.")
        else:
            if gpa_credits > 0:
                st.success(f"🎯 **GPA for Semester {semester_number}: {gpa:.2f}**")
            else:
                st.info(f"🎯 **GPA for Semester {semester_number}: 0.00**")
                st.info("GPA cannot be calculated as only non-graded courses were selected.")
            
        if total_credits <= MAX_CREDITS:
            display_results_table(calculated_subjects)