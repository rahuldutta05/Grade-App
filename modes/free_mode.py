import streamlit as st
from utils import calculate_gpa, GRADE_POINTS
from components.tables import display_results_table

GRADE_OPTIONS = list(GRADE_POINTS.keys())
NON_GRADED_OPTIONS = ["P", "F"]

def add_row(idx):
    new_row = {
        "id": st.session_state.next_id,
        "course_display": None,
        "grade": "S"
    }
    st.session_state.rows.insert(idx + 1, new_row)
    st.session_state.next_id += 1

def delete_row(row_id):
    if len(st.session_state.rows) > 1:
        st.session_state.rows = [r for r in st.session_state.rows if r["id"] != row_id]

def run(MAX_TOTAL_CREDITS, courses_df):
    st.header("Free Mode – Flexible GPA Calculator 🎓")
    st.caption("Add any courses, choose grades, and compute GPA within your total credit limit.")

    # Init rows
    if "rows" not in st.session_state:
        st.session_state.rows = [{"id": 0, "course_display": None, "grade": "S"}]
        st.session_state.next_id = 1

    selected_courses = [
        row["course_display"]
        for row in st.session_state.rows
        if row["course_display"]
    ]

    # Header
    header = st.columns([0.5, 3, 2, 1, 1, 0.5])
    header[0].write("")
    header[1].markdown("**Course**")
    header[2].markdown("**Type**")
    header[3].markdown("**Credits**")
    header[4].markdown("**Grade**")
    header[5].write("")

    calculated = []

    for idx, row in enumerate(st.session_state.rows):
        row_id = row["id"]

        add_col, course_col, type_col, credits_col, grade_col, del_col = st.columns(
            [0.5, 3, 2, 1, 1, 0.5]
        )
        with add_col:
            st.button("➕", key=f"add_{row_id}", on_click=add_row, args=(idx,))
        with course_col:
            available_courses = sorted(courses_df["Display"].tolist())
            options_available = [
                c for c in available_courses
                if c not in selected_courses or c == row["course_display"]
            ]

            current = row["course_display"]
            idx_val = options_available.index(current) if current in options_available else None

            selected = st.selectbox(
                "Course",
                key=f"course_{row_id}",
                options=options_available,
                index=idx_val,
                label_visibility="collapsed",
                placeholder="Select a course..."
            )
            row["course_display"] = selected

        if row["course_display"]:
            df_row = courses_df[courses_df["Display"] == row["course_display"]].iloc[0]
            ctype = df_row["Type"]
            credits = float(df_row["Credits"])
            is_nongraded = "Non-Graded" in ctype
        else:
            ctype = ""
            credits = 0.0
            is_nongraded = False

        with type_col:
            st.text_input("", value=ctype, disabled=True, label_visibility="collapsed")

        with credits_col:
            st.number_input(
                "",
                value=credits,
                disabled=True,
                format="%.1f",
                key=f"cred_{row_id}",
                label_visibility="collapsed"
            )

        with grade_col:
            valid_grades = NON_GRADED_OPTIONS if is_nongraded else GRADE_OPTIONS
            if row["grade"] not in valid_grades:
                row["grade"] = valid_grades[0]

            grade = st.selectbox(
                "",
                options=valid_grades,
                key=f"grade_{row_id}",
                index=valid_grades.index(row["grade"]),
                label_visibility="collapsed"
            )
            row["grade"] = grade

        with del_col:
            st.button("➖", key=f"delete_{row_id}", on_click=delete_row, args=(row_id,))

        if row["course_display"]:
            calculated.append({
                "Course": row["course_display"],
                "Type": ctype,
                "Credits": credits,
                "Grade": grade,
            })

    if calculated:
        st.markdown("---")
        st.subheader("Results")

        total_credits = sum(sub["Credits"] for sub in calculated)
        graded_only = [sub for sub in calculated if "Non-Graded" not in sub["Type"]]

        gpa, gpa_credits = calculate_gpa(graded_only)

        st.info(f"📘 **Total Credits Selected:** {total_credits:.2f}")
        st.info(f"📗 **GPA Credits (Graded):** {gpa_credits:.2f}")

        if total_credits > MAX_TOTAL_CREDITS:
            st.error(
                f"⚠️ Total credits exceed your program limit of {MAX_TOTAL_CREDITS}. "
                f"Please remove some courses."
            )
        else:
            st.success(f"🎯 **GPA (Free Mode): {gpa:.2f}**")

        display_results_table(calculated)
