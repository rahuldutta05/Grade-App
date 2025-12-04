import os
import math
import streamlit as st
import numpy as np
import joblib
import matplotlib.pyplot as plt

GRADE_MAP = {
    0: "F",
    1: "E",
    2: "D",
    3: "C",
    4: "B",
    5: "A",
    6: "S"
}

GRADE_COLORS = {
    "S": "#16a34a",
    "A": "#22c55e",
    "B": "#f4b850",
    "C": "#da6e21",
    "D": "#b95401",
    "E": "#c5374e",
    "F": "#fc0202"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_models():
    """Load models from the same directory as this file."""
    try:
        avg_path = os.path.join(BASE_DIR, "class_avg_xgb.pkl")
        sd_path = os.path.join(BASE_DIR, "class_sd_xgb.pkl")
        grade_path = os.path.join(BASE_DIR, "grade_xgb_classifier.pkl")

        reg_avg = joblib.load(avg_path)
        reg_sd = joblib.load(sd_path)
        clf_grade = joblib.load(grade_path)
        return reg_avg, reg_sd, clf_grade
    except FileNotFoundError as e:
        st.error(f"Model file not found: {e.filename}")
        st.error("Place class_avg_xgb.pkl, class_sd_xgb.pkl and grade_xgb_classifier.pkl beside this file.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading models: {e}")
        st.stop()

regressor_avg, regressor_sd, classifier_grade = load_models()

def calculate_weighted_marks(cat1, cat2, da1, da2, da3, fat):
    """Return overall weighted marks (out of 100)."""
    return (cat1 / 50) * 15 + (cat2 / 50) * 15 + \
           (da1 / 10) * 10 + (da2 / 10) * 10 + (da3 / 10) * 10 + \
           (fat / 100) * 40

def safe_mean(values):
    vals = [v for v in values if v is not None and v > 0]
    return np.mean(vals) if vals else None

def get_lab_grade(total_marks):
    """Fixed mapping for lab courses (60+40 format)."""
    final = math.ceil(total_marks)
    if final >= 90: return "S"
    if final >= 80: return "A"
    if final >= 70: return "B"
    if final >= 60: return "C"
    if final >= 50: return "D"
    if final >= 40: return "E"
    return "F"

def apply_hard_rules(overall, fat, predicted_grade):
    """
    Mandatory overrides:
    - overall < 50 => F
    - fat < 40 => F
    - predicted S but overall < 80 => demote to A
    """
    if overall < 50:
        return "F"
    if fat < 40:
        return "F"
    if predicted_grade == "S" and overall < 80:
        return "A"
    return predicted_grade

def zscore_to_grade(final_marks, class_avg, class_sd):
    if class_sd == 0:
        return "S" if final_marks >= class_avg else "F"

    z = (final_marks - class_avg) / class_sd

    if z >= 2.25:
        return "S"
    elif z >= 1.75:
        return "S"
    elif z >= 1.25:
        return "A"
    elif z >= 0.75:
        return "A"
    elif z >= 0.25:
        return "B"
    elif z >= -0.25:
        return "B"
    elif z >= -0.75:
        return "C"
    elif z >= -1.25:
        return "C"
    elif z >= -1.75:
        return "D"
    elif z >= -2.25:
        return "D"
    elif z >= -2.75:
        return "E"
    elif z >= -3.25:
        return "E"
    else:
        return "F"

def plot_bell_curve(class_mean, class_sd, user_score):
    """
    Returns a matplotlib figure with a normal distribution curve
    and a vertical line marking user_score.
    (No seaborn - plain matplotlib)
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    width = max(8 * (class_sd if class_sd > 0 else 1), 20)
    x = np.linspace(class_mean - width/2, class_mean + width/2, 1000)
    if class_sd <= 0:
        y = np.zeros_like(x)
        idx = np.argmin(np.abs(x - class_mean))
        y[idx] = 1.0
    else:
        y = (1 / (class_sd * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - class_mean) / class_sd) ** 2)

    ax.plot(x, y)
    ax.fill_between(x, 0, y, alpha=0.15)
    ax.axvline(class_mean, linestyle="--", linewidth=1, label=f"Class Mean = {class_mean:.2f}")
    ax.axvline(user_score, linestyle="-", linewidth=2, label=f"Your Score = {user_score:.2f}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Density")
    ax.legend(loc="upper right", fontsize="small")
    ax.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    return fig

def show_grade_card(letter_grade, overall, class_mean, class_sd, model_used):
    color = GRADE_COLORS.get(letter_grade, "#64748b")
    st.markdown(f"""
        <div style="display:flex; gap:12px; align-items:center">
            <div style="background:{color}; color:white; padding:12px 18px; border-radius:8px; min-width:120px; text-align:center;">
                <div style="font-size:22px; font-weight:700">{letter_grade}</div>
                <div style="font-size:12px; opacity:0.9">Predicted Grade</div>
            </div>
            <div style="flex:1;">
                <div style="font-weight:600">Overall Score: <span style='font-weight:700'>{overall:.2f}</span></div>
                <div>Class Mean: <span style='font-weight:700'>{class_mean:.2f}</span> &nbsp; • &nbsp; Class SD: <span style='font-weight:700'>{class_sd:.2f}</span></div>
                <div style="margin-top:6px; font-size:13px; color:#475569">Model: {model_used}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def progress_to_next(letter_grade, overall, class_mean, class_sd):
    """
    Compute a simple 'progress' metric toward the next higher grade.
    We'll map letter grades to z-thresholds and compute how far the user's z is
    between current letter lower bound and the next higher letter lower bound.
    """
    if class_sd == 0:
        return 1.0

    z = (overall - class_mean) / class_sd

    lower_bounds = {
        "S": 2.25,
        "A": 1.25,
        "B": 0.25,
        "C": -0.75,
        "D": -1.75,
        "E": -2.75,
        "F": -999.0
    }

    order = ["F", "E", "D", "C", "B", "A", "S"]

    if letter_grade not in order:
        return 0.0

    idx = order.index(letter_grade)
    if letter_grade == "S":
        min_z = lower_bounds["S"]
        prog = min(1.0, (z - min_z) / 2.0) if z >= min_z else 0.0
        return max(0.0, prog)

    next_letter = order[idx + 1]
    lower_current = lower_bounds[letter_grade]
    lower_next = lower_bounds[next_letter]

    denom = (lower_next - lower_current)
    if denom == 0:
        return 0.0
    prog = (z - lower_current) / denom
    return float(np.clip(prog, 0.0, 1.0))

def ml_predict_final_grade(
    da1, da2, da3, cat1, cat2, fat,
    da1_avg, da2_avg, da3_avg, cat1_avg, cat2_avg, fat_avg,
    class_strength
):
    """Predict class_mean, class_sd, and final grade using ML models."""
    overall = calculate_weighted_marks(cat1, cat2, da1, da2, da3, fat)

    provided_avgs = [da1_avg, da2_avg, da3_avg, cat1_avg, cat2_avg, fat_avg]
    known_avg = safe_mean(provided_avgs)

    if known_avg is not None:
        da_vals = [v for v in [da1_avg, da2_avg, da3_avg] if v and v > 0]
        cat_vals = [v for v in [cat1_avg, cat2_avg] if v and v > 0]

        da_mean = np.mean(da_vals) if da_vals else safe_mean([da1, da2, da3])
        cat_mean = np.mean(cat_vals) if cat_vals else safe_mean([cat1, cat2])
        fat_mean = fat_avg if fat_avg and fat_avg > 0 else fat

        class_mean = calculate_weighted_marks(cat_mean, cat_mean, da_mean, da_mean, da_mean, fat_mean)
    else:
        try:
            class_mean = regressor_avg.predict([[da1, da2, da3, cat1, cat2, fat, class_strength]])[0]
        except Exception:
            class_mean = regressor_avg.predict([[da1, da2, da3, cat1, cat2, fat]])[0]

    try:
        class_sd = regressor_sd.predict([[overall, class_mean, class_strength]])[0]
    except Exception:
        class_sd = regressor_sd.predict([[overall, class_mean]])[0]

    try:
        grade_id = classifier_grade.predict([[overall, class_mean, class_sd, class_strength]])[0]
    except Exception:
        grade_id = classifier_grade.predict([[overall, class_mean, class_sd]])[0]

    predicted_letter = GRADE_MAP.get(int(grade_id), "Unknown")
    final_letter = apply_hard_rules(overall, fat, predicted_letter)

    return overall, class_mean, class_sd, final_letter

def run(courses_df):
    st.set_page_config(page_title="Grade Predictor (Advanced)", layout="centered")
    st.header("Grade Prediction — Advanced Mode")
    st.write("Use ML or manual override (Z-score). Visuals include a bell curve and progress to next grade.")

    course_list = ["--Select--"] + sorted(courses_df["Display"].tolist())
    course_selected = st.selectbox("Select Course", course_list)

    if course_selected == "--Select--":
        st.info("Choose a course to start predicting grades.")
        return

    selected_df = courses_df[courses_df["Display"] == course_selected]
    if selected_df.empty:
        st.error("Selected course not found in course list.")
        return

    course_code = selected_df["Course Code"].iloc[0]
    is_lab = course_code.endswith("P") or course_code.endswith("E")

    if is_lab:
        st.subheader("Lab Course (Fixed scale)")
        lab_marks = st.number_input("Lab Marks (out of 60)", min_value=0, max_value=60, value=0)
        fat_marks = st.number_input("FAT Marks (out of 40)", min_value=0, max_value=40, value=0)

        if st.button("Predict Grade"):
            overall = lab_marks + fat_marks

            final = get_lab_grade(overall)

            st.success(f"Total Score: {overall:.2f}")
            show_grade_card(final, overall, overall, 0.0, "Lab Rule-based")

        return

    st.subheader("Theory Course Components")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Your Marks")
        cat1 = st.number_input("CAT 1 (out of 50)", 0, 50, value=0)
        cat2 = st.number_input("CAT 2 (out of 50)", 0, 50, value=0)
        da1 = st.number_input("DA 1 (out of 10)", 0, 10, value=0)
        da2 = st.number_input("DA 2 (out of 10)", 0, 10, value=0)
        da3 = st.number_input("DA 3 (out of 10)", 0, 10, value=0)
        fat = st.number_input("FAT (out of 100)", 0, 100, value=0)

    with col2:
        st.markdown("### Averages (optional)")
        cat1_avg = st.number_input("CAT 1 Avg", 0.0, 50.0, 0.0)
        cat2_avg = st.number_input("CAT 2 Avg", 0.0, 50.0, 0.0)
        da1_avg = st.number_input("DA 1 Avg", 0.0, 10.0, 0.0)
        da2_avg = st.number_input("DA 2 Avg", 0.0, 10.0, 0.0)
        da3_avg = st.number_input("DA 3 Avg", 0.0, 10.0, 0.0)
        fat_avg = st.number_input("FAT Avg", 0.0, 100.0, 0.0)

    st.markdown("---")
    st.markdown("### Manual Override (Skip ML)")
    st.caption("⚠️ If you enter BOTH Overall Class Average and Class SD, **all component averages will be ignored** and ML will be skipped.")
    ov_col, sd_col = st.columns(2)
    with ov_col:
        manual_avg = st.number_input("Overall Class Average (Optional)", 0.0, 100.0, 0.0)
    with sd_col:
        manual_sd = st.number_input("Class SD (Optional)", 0.0, 40.0, 0.0)

    class_strength = st.number_input("Class Strength (for ML models)", 10, 120, 60)

    if st.button("Predict Grade"):
        overall = calculate_weighted_marks(cat1, cat2, da1, da2, da3, fat)

        if manual_avg > 0 and manual_sd > 0:
            st.info("Manual override active — component averages ignored, ML skipped.")
            predicted = zscore_to_grade(overall, manual_avg, manual_sd)
            final = apply_hard_rules(overall, fat, predicted)

            show_grade_card(final, overall, manual_avg, manual_sd, "Manual (Z-score)")
            prog = progress_to_next(final, overall, manual_avg, manual_sd)
            st.progress(prog)
            fig = plot_bell_curve(manual_avg, manual_sd, overall)
            st.pyplot(fig)
            return

        if manual_avg > 0 and manual_sd == 0:
            st.info("Manual overall class average provided — component averages ignored for class mean.")
            class_mean = manual_avg
            try:
                class_sd = regressor_sd.predict([[overall, class_mean, class_strength]])[0]
            except Exception:
                class_sd = regressor_sd.predict([[overall, class_mean]])[0]
            try:
                grade_id = classifier_grade.predict([[overall, class_mean, class_sd, class_strength]])[0]
            except Exception:
                grade_id = classifier_grade.predict([[overall, class_mean, class_sd]])[0]

            predicted = GRADE_MAP.get(int(grade_id), "Unknown")
            final = apply_hard_rules(overall, fat, predicted)

            show_grade_card(final, overall, class_mean, class_sd, "ManualAvg + ML")
            prog = progress_to_next(final, overall, class_mean, class_sd)
            st.progress(prog)
            fig = plot_bell_curve(class_mean, class_sd, overall)
            st.pyplot(fig)
            return

        if manual_avg == 0 and manual_sd > 0:
            st.info("Manual class SD provided — component averages ignored for SD handling where appropriate.")
            try:
                class_mean = regressor_avg.predict([[da1, da2, da3, cat1, cat2, fat, class_strength]])[0]
            except Exception:
                class_mean = regressor_avg.predict([[da1, da2, da3, cat1, cat2, fat]])[0]

            class_sd = manual_sd

            try:
                grade_id = classifier_grade.predict([[overall, class_mean, class_sd, class_strength]])[0]
            except Exception:
                grade_id = classifier_grade.predict([[overall, class_mean, class_sd]])[0]

            predicted = GRADE_MAP.get(int(grade_id), "Unknown")
            final = apply_hard_rules(overall, fat, predicted)

            show_grade_card(final, overall, class_mean, class_sd, "ManualSD + ML")
            prog = progress_to_next(final, overall, class_mean, class_sd)
            st.progress(prog)
            fig = plot_bell_curve(class_mean, class_sd, overall)
            st.pyplot(fig)
            return

        st.info("No manual override — using ML models (component averages used if provided).")

        overall, class_mean, class_sd, predicted = ml_predict_final_grade(
            da1, da2, da3, cat1, cat2, fat,
            da1_avg, da2_avg, da3_avg, cat1_avg, cat2_avg, fat_avg,
            class_strength
        )

        final = apply_hard_rules(overall, fat, predicted)

        show_grade_card(final, overall, class_mean, class_sd, "ML")
        prog = progress_to_next(final, overall, class_mean, class_sd)
        st.progress(prog)
        fig = plot_bell_curve(class_mean, class_sd, overall)
        st.pyplot(fig)
        return
