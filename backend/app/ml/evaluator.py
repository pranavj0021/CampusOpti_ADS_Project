import numpy as np
from typing import Dict
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class ModelEvaluator:
    @staticmethod
    def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculates standard regression evaluation metrics: MAE, RMSE, R2.
        """
        mae = float(mean_absolute_error(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_true, y_pred))

        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4)
        }
