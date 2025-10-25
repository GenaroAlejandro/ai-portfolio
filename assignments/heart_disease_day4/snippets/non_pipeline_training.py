# Non-pipeline training snippet (LogReg, RF, SVM, KNN)
# Prints classification_report only.

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

from sklearn.metrics import classification_report

# --- Load data (assumes repo structure used in the assignment) ---
CSV = "../data/heart_disease.csv"  # run from snippets/ or adjust path if needed
df = pd.read_csv(CSV)

# Unify column name if needed
if "thalch" in df.columns and "thalach" not in df.columns:
    df = df.rename(columns={"thalch": "thalach"})

# 1) Features/target
X = df.drop(columns=['num', 'id', 'dataset'])
# Binary medical framing: 0 = no disease, 1 = any disease
# y = (df['num'] > 0).astype(int)
# Multiclass
y = df['num']

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Manual preprocessing (NO Pipeline)
cat_cols = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]
num_cols = [c for c in X_train.columns if c not in cat_cols]

# Numeric: impute -> scale
num_imp = SimpleImputer(strategy="mean")
Xtr_num = num_imp.fit_transform(X_train[num_cols])
Xte_num = num_imp.transform(X_test[num_cols])

scaler = StandardScaler()
Xtr_num = scaler.fit_transform(Xtr_num)
Xte_num = scaler.transform(Xte_num)

# Categorical: impute -> one-hot
cat_imp = SimpleImputer(strategy="most_frequent")
Xtr_cat = cat_imp.fit_transform(X_train[cat_cols])
Xte_cat = cat_imp.transform(X_test[cat_cols])

try:
    ohe = OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)
except TypeError:
    ohe = OneHotEncoder(drop="first", handle_unknown="ignore", sparse=False)

Xtr_cat = ohe.fit_transform(Xtr_cat)
Xte_cat = ohe.transform(Xte_cat)

# Combine
Xtr = np.hstack([Xtr_num, Xtr_cat])
Xte = np.hstack([Xte_num, Xte_cat])

# Models
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=300, random_state=42),
    "SVM": SVC(random_state=42),
    "KNN": KNeighborsClassifier(),
}

# Train & print reports
for name, clf in models.items():
    clf.fit(Xtr, y_train)
    preds = clf.predict(Xte)
    print(f"\n=== {name} ===")
    # For Binary class, you can add 'target_names' target_names=['No Disease','Disease']
    print(classification_report(y_test, preds, zero_division=0))

    
