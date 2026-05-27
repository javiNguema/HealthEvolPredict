# analysis.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Tuple, Optional


def perform_pca(df: pd.DataFrame, npca: int = 2, col_missing_threshold: float = 0.50) -> Tuple[Optional[np.ndarray], Optional[PCA], Optional[list]]:
    """
    Perform PCA safely by discarding highly incomplete columns and low-count missing rows.
    
    Parameters:
    - df: Input pandas DataFrame
    - npca: Number of principal components to calculate
    - col_missing_threshold: Discard any column if more than this % of data is missing (default 50%)
    """
    if df is None or df.empty:
        return None, None, None

    # 1. Isolate numeric columns
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    
    # Handle infinite values as missing data to keep calculations stable
    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)

    if numeric_df.shape[1] < 2:
        return None, None, None

    # 2. DISCARD COLUMN IF MISSINGNESS IS HUGE
    # Calculates the proportion of missing entries per column
    missing_proportions = numeric_df.isna().mean()
    
    # Keep only columns that don't exceed our threshold (e.g., completely empty or >50% empty)
    valid_cols = missing_proportions[missing_proportions <= col_missing_threshold].index.tolist()
    filtered_df = numeric_df[valid_cols]

    # 3. DROP ROWS IF MISSING DATA IS REASONABLY LOW
    # Now that completely/largely empty columns are gone, drop rows containing remaining sporadic NaNs
    cleaned_df = filtered_df.dropna()

    # 4. CRITICAL CHECK: Ensure we still have samples and columns left to execute a valid PCA
    if cleaned_df.shape[0] < 2 or cleaned_df.shape[1] < 2:
        print(f"PCA Aborted: Matrix unstable after filtering. Remaining shape: {cleaned_df.shape}")
        return None, None, None

    feature_names = cleaned_df.columns.tolist()

    # 5. Estandarización y Escalado Seguro (No extrapolation/imputation used)
    scaler = StandardScaler()
    try:
        scaled_data = scaler.fit_transform(cleaned_df)
        
        # Adjust components to not exceed remaining samples or features
        actual_components = min(npca, cleaned_df.shape[0], cleaned_df.shape[1])
        if actual_components < 2:
            return None, None, None

        # 6. Run PCA
        pca = PCA(n_components=actual_components)
        pca_result = pca.fit_transform(scaled_data)
        
        return pca_result, pca, feature_names

    except Exception as e:
        print(f"Error executing PCA mathematics: {e}")
        return None, None, None




if __name__ == "__main__":
    ...