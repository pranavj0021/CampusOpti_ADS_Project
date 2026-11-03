import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.preprocessing import StandardScaler

class CampusDataPreprocessor:
    """
    Handles data validation, feature engineering, and encoding for enrollment
    and resource demand forecasting.
    """
    def __init__(self):
        self.scaler = StandardScaler()
        self.dept_encoding: Dict[str, int] = {}
        self.reverse_dept_encoding: Dict[int, str] = {}
        self.feature_names: List[str] = []

    def fit_transform_enrollment(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        Takes raw student enrollment dataframe, cleans it, engineers features,
        and prepares X, y for chronological training.
        """
        # Ensure correct column types
        clean_df = df.copy()
        clean_df["total_students"] = pd.to_numeric(clean_df["total_students"], errors="coerce").fillna(0)
        clean_df["year_level"] = pd.to_numeric(clean_df.get("year_level", 1), errors="coerce").fillna(1)
        clean_df["divisions_count"] = pd.to_numeric(clean_df.get("divisions_count", 1), errors="coerce").fillna(1)

        # Parse start year from academic_year string (e.g., '2023-2024' -> 2023)
        def parse_year(yr_str):
            try:
                return int(str(yr_str).split("-")[0])
            except Exception:
                return 2024

        clean_df["start_year"] = clean_df["academic_year"].apply(parse_year)
        clean_df = clean_df.sort_values(by=["department_code", "start_year"]).reset_index(drop=True)

        # Department categorical encoding
        unique_depts = sorted(clean_df["department_code"].unique().tolist())
        self.dept_encoding = {dept: idx for idx, dept in enumerate(unique_depts)}
        self.reverse_dept_encoding = {idx: dept for dept, idx in self.dept_encoding.items()}
        clean_df["dept_code_num"] = clean_df["department_code"].map(self.dept_encoding)

        # Feature Engineering:
        # 1. Year sequence index
        min_year = clean_df["start_year"].min()
        clean_df["year_idx"] = clean_df["start_year"] - min_year

        # 2. Lag features (previous year total enrollment for that dept)
        dept_yearly = clean_df.groupby(["department_code", "start_year"])["total_students"].sum().reset_index()
        dept_yearly["prev_year_students"] = dept_yearly.groupby("department_code")["total_students"].shift(1)
        
        # Calculate historical enrollment growth rate (%)
        dept_yearly["growth_rate"] = (
            (dept_yearly["total_students"] - dept_yearly["prev_year_students"]) / 
            dept_yearly["prev_year_students"].replace(0, np.nan)
        ).fillna(0.05)

        # Merge back
        clean_df = clean_df.merge(
            dept_yearly[["department_code", "start_year", "prev_year_students", "growth_rate"]],
            on=["department_code", "start_year"],
            how="left"
        )
        clean_df["prev_year_students"] = clean_df["prev_year_students"].fillna(clean_df["total_students"])
        clean_df["growth_rate"] = clean_df["growth_rate"].fillna(0.05)

        # 3. Semester indicator
        clean_df["is_fall"] = clean_df["semester"].apply(lambda s: 1 if str(s).lower() == "fall" else 0)

        # Define feature matrix
        self.feature_names = [
            "dept_code_num",
            "start_year",
            "year_idx",
            "year_level",
            "prev_year_students",
            "growth_rate",
            "divisions_count",
            "is_fall"
        ]

        X = clean_df[self.feature_names].values
        y = clean_df["total_students"].values

        return X, y, clean_df

    def transform_inference(self, depts: List[str], target_academic_year: str, latest_history_df: pd.DataFrame) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Builds feature vectors for forecasting future academic year.
        """
        start_year = int(target_academic_year.split("-")[0])
        min_year = 2019
        year_idx = start_year - min_year

        rows = []
        meta_list = []

        for dept in depts:
            dept_num = self.dept_encoding.get(dept, 0)
            
            # Lookup latest available enrollment for this department
            dept_data = latest_history_df[latest_history_df["department_code"] == dept]
            if not dept_data.empty:
                last_year = dept_data["start_year"].max()
                last_subset = dept_data[dept_data["start_year"] == last_year]
                last_total = last_subset["total_students"].sum()
                avg_growth = dept_data["growth_rate"].mean() if "growth_rate" in dept_data.columns else 0.05
            else:
                last_total = 200
                avg_growth = 0.05

            for lvl in [1, 2, 3, 4]:
                lvl_data = dept_data[dept_data["year_level"] == lvl]
                lvl_students = lvl_data["total_students"].iloc[-1] if not lvl_data.empty else int(last_total / 4)
                
                feat = [
                    dept_num,
                    start_year,
                    year_idx,
                    lvl,
                    lvl_students,
                    avg_growth,
                    max(1, int(lvl_students / 60)),
                    1 # Fall
                ]
                rows.append(feat)
                meta_list.append({
                    "department_code": dept,
                    "year_level": lvl,
                    "target_year": target_academic_year,
                    "base_students": lvl_students,
                    "historical_growth": float(avg_growth)
                })

        return np.array(rows), meta_list
