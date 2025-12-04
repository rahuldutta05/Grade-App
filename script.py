import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
from xgboost import XGBRegressor, XGBClassifier
import joblib
import math

# ============ 1. Load Data ============
df = pd.read_csv("data/grades.csv")
df.columns = df.columns.str.strip()

# ============ 2. Weighted Score ============
def calculate_weighted_marks(cat1, cat2, da1, da2, da3, fat):
    return (cat1 / 50) * 15 + (cat2 / 50) * 15 + \
           (da1 / 10) * 10 + (da2 / 10) * 10 + (da3 / 10) * 10 + \
           (fat / 100) * 40

df["Overall Score"] = df.apply(lambda r: calculate_weighted_marks(
    r["Continuous Assessment I"],
    r["Continuous Assessment II"],
    r["Digital Assignment I"],
    r["Digital Assignment II"],
    r["Digital Assignment III"],
    r["Final Assessment Test"]
), axis=1)

# Encode grades
grade_map = {"F": 0, "E": 1, "D": 2, "C": 3, "B": 4, "A": 5, "S": 6}
inv_grade_map = {v: k for k, v in grade_map.items()}
df["Final Grade Encoded"] = df["Final Grade"].map(grade_map)

# ============================================================================================
# 3A — Model 1: Predict Class Mean   (Inputs: DA1–DA3, CAT1–CAT2, FAT, Class Strength)
# ============================================================================================
print("\n📘 Training Class Mean Model...")

X_avg = df[
    [
        "Digital Assignment I", "Digital Assignment II", "Digital Assignment III",
        "Continuous Assessment I", "Continuous Assessment II", "Final Assessment Test",
        "Class Strength"
    ]
]
y_avg = df["Class Mean"]

X_train, X_test, y_train, y_test = train_test_split(X_avg, y_avg, test_size=0.2, random_state=42)

regressor_avg = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
regressor_avg.fit(X_train, y_train)

y_pred = regressor_avg.predict(X_test)
print(f"R² Score: {r2_score(y_test, y_pred):.3f}")
print(f"RMSE: {math.sqrt(mean_squared_error(y_test, y_pred)):.3f}")

# ============================================================================================
# 3B — Model 2: Predict Class SD   (Inputs: Overall Score, Class Mean, Class Strength)
# ============================================================================================
print("\n📗 Training Class SD Model...")

X_sd = df[["Overall Score", "Class Mean", "Class Strength"]]
y_sd = df["Class SD"]

X_train_sd, X_test_sd, y_train_sd, y_test_sd = train_test_split(
    X_sd, y_sd, test_size=0.2, random_state=42
)

regressor_sd = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
regressor_sd.fit(X_train_sd, y_train_sd)

y_pred_sd = regressor_sd.predict(X_test_sd)
print(f"R² Score: {r2_score(y_test_sd, y_pred_sd):.3f}")
print(f"RMSE: {math.sqrt(mean_squared_error(y_test_sd, y_pred_sd)):.3f}")

# ============================================================================================
# 3C — Model 3: Predict Final Grade (Inputs: Overall Score, Class Mean, Class SD, Class Strength)
# ============================================================================================
print("\n📙 Training Final Grade Classifier...")

X_grade = df[["Overall Score", "Class Mean", "Class SD", "Class Strength"]]
y_grade = df["Final Grade Encoded"]

Xg_train, Xg_test, yg_train, yg_test = train_test_split(
    X_grade, y_grade, test_size=0.2, random_state=42, stratify=y_grade
)

classifier_grade = XGBClassifier(
    n_estimators=400, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
classifier_grade.fit(Xg_train, yg_train)

yg_pred = classifier_grade.predict(Xg_test)

print("Accuracy:", accuracy_score(yg_test, yg_pred))
print("\nClassification Report:\n", classification_report(yg_test, yg_pred))

# ============================================================================================
# 4. SAVE MODELS
# ============================================================================================
print("\n💾 Saving trained models...")

joblib.dump(regressor_avg, "class_avg_xgb.pkl")
joblib.dump(regressor_sd, "class_sd_xgb.pkl")
joblib.dump(classifier_grade, "grade_xgb_classifier.pkl")
joblib.dump(grade_map, "grade_mapping.pkl")

print("✅ All models saved successfully!")
