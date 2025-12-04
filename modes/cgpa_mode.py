import streamlit as st
import pandas as pd
from typing import List, Dict

MAX_SEM_CREDITS = 30.5
TOTAL_SEMESTERS = 8

def run(MAX_TOTAL_CREDITS):
    st.subheader("CGPA Calculator")
    
    if "semesters" not in st.session_state:
        st.session_state.semesters = [{"id": 0, "gpa": None, "credits": None}]
        st.session_state.next_sem_id = 1
    
    if 'show_goal_input' not in st.session_state:
        st.session_state.show_goal_input = False
    
    if 'goal_cgpa' not in st.session_state:
        st.session_state.goal_cgpa = None

    def add_semester_row():
        if len(st.session_state.semesters) < TOTAL_SEMESTERS:
            new_id = st.session_state.next_sem_id
            st.session_state.semesters.append({"id": new_id, "gpa": None, "credits": None})
            st.session_state.next_sem_id += 1

    def delete_semester_row(row_id):
        if len(st.session_state.semesters) > 1:
            st.session_state.semesters = [sem for sem in st.session_state.semesters if sem["id"] != row_id]

    def increment_credits(sem_id):
        sem_data = next((s for s in st.session_state.semesters if s["id"] == sem_id), None)
        if sem_data:
            current_credits = sem_data["credits"] or 0.0
            new_credits = current_credits + 0.5
            if new_credits <= MAX_SEM_CREDITS:
                sem_data["credits"] = new_credits
                st.session_state[f"credits_{sem_id}"] = new_credits

    def decrement_credits(sem_id):
        sem_data = next((s for s in st.session_state.semesters if s["id"] == sem_id), None)
        if sem_data:
            current_credits = sem_data["credits"] or 0.0
            new_credits = current_credits - 0.5
            if new_credits >= 0.0:
                sem_data["credits"] = new_credits
                st.session_state[f"credits_{sem_id}"] = new_credits
    
    def round_credits(sem_id):
        if f"credits_{sem_id}" in st.session_state:
            val = st.session_state[f"credits_{sem_id}"]
            if val is not None:
                rounded_val = round(val * 2) / 2
                st.session_state[f"credits_{sem_id}"] = rounded_val
                sem_data = next((s for s in st.session_state.semesters if s["id"] == sem_id), None)
                if sem_data:
                    sem_data["credits"] = rounded_val

    st.markdown("##### Enter your past semester details:")
    col1, col2, col3 = st.columns([1, 1, 0.5])
    with col1:
        st.markdown("##### GPA")
    with col2:
        st.markdown("##### Credits")
    with col3:
        st.markdown("##### ")

    gpas_valid = True

    for idx, sem in enumerate(st.session_state.semesters):
        gpa_col, credits_col, del_col = st.columns([1, 1, 0.5])
        
        with gpa_col:
            gpa_key = f"gpa_{sem['id']}"
            gpa_value = st.text_input(
                f"Semester {idx + 1} GPA",
                value=f"{sem['gpa']:.2f}" if sem['gpa'] is not None else "",
                key=f"{gpa_key}_text_input",
                label_visibility="collapsed"
            )
            try:
                if gpa_value:
                    sem["gpa"] = float(gpa_value)
                    if not (0.0 <= sem["gpa"] <= 10.0):
                        st.toast("GPA must be between 0.00 and 10.00")
                        gpas_valid = False
            except ValueError:
                st.toast("Invalid GPA. Please enter a number.")
                gpas_valid = False
        
        with credits_col:
            credits_val = st.number_input(
                f"Semester {idx + 1} Credits",
                min_value=0.0,
                max_value=MAX_SEM_CREDITS,
                step=0.5,
                format="%.1f",
                key=f"credits_{sem['id']}",
                label_visibility="collapsed",
                value=sem['credits'],
                on_change=round_credits,
                args=(sem['id'],)
            )
            sem["credits"] = credits_val
        
        with del_col:
            is_last_row = len(st.session_state.semesters) <= 1
            st.button("➖", key=f"del_sem_{sem['id']}", on_click=delete_semester_row, args=(sem['id'],), disabled=is_last_row, use_container_width=True)

    if len(st.session_state.semesters) < TOTAL_SEMESTERS:
        st.button("➕ Add Semester", on_click=add_semester_row)
    
    st.markdown("---")
    
    if not gpas_valid:
        st.stop()
    
    valid_semesters = [s for s in st.session_state.semesters if s["gpa"] is not None and s["credits"] is not None]
    
    total_weighted_sum = sum(s["gpa"] * s["credits"] for s in valid_semesters)
    current_total_credits = sum(s["credits"] for s in valid_semesters)
    
    if current_total_credits > MAX_TOTAL_CREDITS:
        st.toast(f"Total credits ({current_total_credits:.1f}) exceed the program limit of {MAX_TOTAL_CREDITS}. Please correct the credits.")
        st.stop()
        
    if current_total_credits > 0:
        cgpa = total_weighted_sum / current_total_credits
        st.success(f"### 🎯 Your Current CGPA: {cgpa:.2f}")

        if cgpa >= 9.0:
            st.balloons()
            st.header("🎉 Congratulations, you're a 9-pointer!")
            st.markdown("""
                You get to enjoy special perks:
                - No 75% attendance criteria
                - First preference in FFCS course registration
            """)
    else:
        st.info("Enter your semester GPAs and credits to calculate your CGPA.")
    
    st.markdown("---")
    
    st.subheader("Achieve a Target CGPA")
    
    if st.button("Set a Target CGPA"):
        st.session_state.show_goal_input = not st.session_state.show_goal_input

    if st.session_state.show_goal_input:
        with st.container(border=True):
            target_cgpa = st.number_input(
                "Enter your target CGPA", 
                min_value=0.0, 
                max_value=10.0, 
                step=0.01, 
                format="%.2f",
                key="target_cgpa_input"
            )
            
            semesters_completed = len(st.session_state.semesters)
            remaining_semesters = TOTAL_SEMESTERS - semesters_completed
            remaining_credits = MAX_TOTAL_CREDITS - current_total_credits
            
            if remaining_semesters > 0 and remaining_credits > 0:
                goal_timeframe = st.radio(
                    "Select timeframe to achieve goal:",
                    ["Next Semester", "Next 2 Semesters", f"Remaining {remaining_semesters} Semesters"],
                    horizontal=True
                )
                
                credits_to_add = 0
                num_sem_to_add = 0

                if goal_timeframe == "Next Semester":
                    num_sem_to_add = 1
                    target_credits = st.number_input(
                        "Credits for Next Semester",
                        min_value=0.0,
                        max_value=remaining_credits if remaining_credits < MAX_SEM_CREDITS else MAX_SEM_CREDITS,
                        step=0.5,
                        format="%.1f",
                        key="target_credits_1"
                    )
                    credits_to_add = target_credits

                elif goal_timeframe == "Next 2 Semesters":
                    num_sem_to_add = 2
                    col_credits_1, col_credits_2 = st.columns(2)
                    with col_credits_1:
                        target_credits_1 = st.number_input(
                            "Credits for Next Semester",
                            min_value=0.0,
                            max_value=remaining_credits,
                            step=0.5,
                            format="%.1f",
                            key="target_credits_2_1"
                        )
                    with col_credits_2:
                        target_credits_2 = st.number_input(
                            "Credits for the Following Semester",
                            min_value=0.0,
                            max_value=remaining_credits - target_credits_1,
                            step=0.5,
                            format="%.1f",
                            key="target_credits_2_2"
                        )
                    credits_to_add = target_credits_1 + target_credits_2

                else:
                    num_sem_to_add = remaining_semesters
                    credits_to_add = remaining_credits
                    st.info(f"The calculation will use your **remaining total credits** of **{remaining_credits:.1f}** for your last {remaining_semesters} semester(s).")
                
                if st.button("Calculate Required GPA"):
                    if current_total_credits == 0:
                        st.toast("Please enter at least one semester's data first.")
                    elif credits_to_add <= 0:
                        st.toast("Please enter a positive number of credits for your target semesters.")
                    else:
                        required_total_weighted_sum = target_cgpa * (current_total_credits + credits_to_add)
                        needed_weighted_sum = required_total_weighted_sum - total_weighted_sum
                        required_gpa = needed_weighted_sum / credits_to_add
                        
                        if required_gpa > 10.0:
                            st.toast(f"It's mathematically impossible to reach a CGPA of {target_cgpa:.2f} from your current position with the chosen credits.")
                        elif required_gpa < 0:
                            st.success(f"You have already surpassed your target CGPA of **{target_cgpa:.2f}**! 🎉")
                        else:
                            st.success(f"To reach a CGPA of **{target_cgpa:.2f}**, you need an average GPA of **{required_gpa:.2f}** in your next {num_sem_to_add} semester(s).")
            else:
                st.toast("You have no remaining semesters or credits to set a goal.")