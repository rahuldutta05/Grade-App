import streamlit as st
import pandas as pd

from utils import get_course_data
import modes.semester_mode as semester_mode
import modes.free_mode as free_mode
import modes.cgpa_mode as cgpa_mode
import modes.grade_prediction_mode as grade_prediction_mode

st.set_page_config(page_title="CGPA Calculator", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { font-size: 1.2em; }
    h1 { font-size: 2.5em; }
    h2 { font-size: 2em; }
    h3 { font-size: 1.8em; }
    h4 { font-size: 1.5em; }

    .stButton > button {
        height: auto;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 1.2em;
    }
</style>
""", unsafe_allow_html=True)

def on_branch_change():
    keys = [
        # Semester Mode
        "rows", "next_id",
        # CGPA Mode
        "semesters", "next_sem_id",
        # Free Mode
        "free_rows", "free_next_id",
        # Timetable (if exists)
        "timetable_rows", "timetable_next_id", "rerun_flag",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

    # Reset mode to default
    st.session_state.mode = "Semester Mode"

def on_mode_change():
    keys = [
        # Semester Mode
        "rows", "next_id",
        # CGPA Mode
        "semesters", "next_sem_id",
        # Free Mode
        "free_rows", "free_next_id",
        # Timetable (if exists)
        "timetable_rows", "timetable_next_id", "rerun_flag",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

def create_navbar(modes):
    cols = st.columns(len(modes))
    current_mode = st.session_state.get("mode", modes[0])

    for i, mode_name in enumerate(modes):
        with cols[i]:
            if st.button(mode_name, key=f"nav_btn_{mode_name}", use_container_width=True):

                if st.session_state.get("mode") != mode_name:
                    on_mode_change()

                st.session_state.mode = mode_name
                current_mode = mode_name

    return current_mode

if "mode" not in st.session_state:
    st.session_state.mode = "Semester Mode"

st.title("🎓 VIT CGPA & GPA Calculator")
st.write("Calculate your GPA and CGPA the right way!")

branch_options = [
    "CSE Core(BCE)",
    "CSE with Specialization in Cyber Physical Systems(BPS)",
    "CSE with Specialization in Artificial Intelligence and Machine Learning(BAI)",
    "CSE with Specialization in Data Science(BDS)",
    "CSE with Specialization in Artificial Intelligence and Robotics(BRS)",
    "Mechatronics(BMH)",
    "Electronics and Communication(BEC)",
    "Electronics and Computer Engineering(BLC)"
]

branch = st.selectbox(
    "Choose Branch",
    branch_options,
    key="branch_selector",
    on_change=on_branch_change
)

if branch == "CSE Core(BCE)":
    course_file_path = "data/courses_bce.csv"
    MAX_TOTAL_CREDITS = 151.0
elif branch == "CSE with Specialization in Cyber Physical Systems(BPS)":
    course_file_path = "data/courses_bps.csv"
    MAX_TOTAL_CREDITS = 151.0
elif branch == "CSE with Specialization in Artificial Intelligence and Machine Learning(BAI)":
    course_file_path = "data/courses_bai.csv"
    MAX_TOTAL_CREDITS = 151.0
elif branch == "CSE with Specialization in Data Science(BDS)":
    course_file_path = "data/courses_bds.csv"
    MAX_TOTAL_CREDITS = 151.0
elif branch == "CSE with Specialization in Artificial Intelligence and Robotics(BRS)":
    course_file_path = "data/courses_brs.csv"
    MAX_TOTAL_CREDITS = 151.0
elif branch == "Mechatronics(BMH)":
    course_file_path = "data/courses_bmh.csv"
    MAX_TOTAL_CREDITS = 154.0
elif branch == "Electronics and Communication(BEC)":
    course_file_path = "data/courses_bec.csv"
    MAX_TOTAL_CREDITS = 151.0
elif branch == "Electronics and Computer Engineering(BLC)":
    course_file_path = "data/courses_blc.csv"
    MAX_TOTAL_CREDITS = 153.0
else:
    course_file_path = "data/courses_bce.csv"
    MAX_TOTAL_CREDITS = 151.0

courses_df = get_course_data(course_file_path)

modes = ["Semester Mode", "CGPA Mode", "Free Mode", "Grade Prediction Mode"]

mode = create_navbar(modes)

if mode == "Semester Mode":
    semester_mode.run(courses_df)

elif mode == "Free Mode":
    free_mode.run(MAX_TOTAL_CREDITS, courses_df)

elif mode == "CGPA Mode":
    cgpa_mode.run(MAX_TOTAL_CREDITS)

elif mode == "Grade Prediction Mode":
    if courses_df is not None:
        grade_prediction_mode.run(courses_df)
    else:
        st.error("Course data could not be loaded. Please check the data file.")

st.markdown("---")
st.markdown("Made with Streamlit")
st.markdown("© 2025 Rahul Dutta")
