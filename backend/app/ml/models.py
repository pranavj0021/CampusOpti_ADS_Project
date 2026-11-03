from typing import Dict, Any
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

def get_candidate_models() -> Dict[str, Any]:
    """
    Returns candidate forecasting models:
    1. Baseline: Linear Regression
    2. Random Forest Regressor
    3. XGBoost Regressor
    """
    return {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=100, 
            max_depth=6, 
            random_state=42
        ),
        "XGBoost": xgb.XGBRegressor(
            n_estimators=120, 
            learning_rate=0.08, 
            max_depth=5, 
            subsample=0.85, 
            random_state=42
        )
    }
