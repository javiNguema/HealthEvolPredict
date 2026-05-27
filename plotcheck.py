import pandas as pd
import numpy as np

def is_plot_compatible(x: pd.Series, y: pd.Series) -> bool:
    """
    Returns True if x and y can be meaningfully plotted together.

    Conditions:
    - Same length
    - After removing NaNs/empty values → still have data
    - Types are compatible:
        numeric-numeric
        numeric-categorical
        categorical-numeric
        categorical-categorical
    """

    # 1. Length check
    if len(x) != len(y):
        return False

    # 2. Combine and clean missing values
    df = pd.DataFrame({'x': x, 'y': y})

    # Treat empty strings as NaN (important for object dtype)
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Drop rows where either is missing
    df = df.dropna()

    # If nothing left → not plottable
    if df.empty:
        return False

    x_clean = df['x']
    y_clean = df['y']

    # 3. Type detection
    def is_numeric(s):
        return pd.api.types.is_numeric_dtype(s)

    def is_categorical(s):
        return pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s) # type: ignore

    x_num = is_numeric(x_clean)
    y_num = is_numeric(y_clean)

    x_cat = is_categorical(x_clean)
    y_cat = is_categorical(y_clean)

    # 4. Compatibility logic (generic, not plot-specific)
    if (x_num or x_cat) and (y_num or y_cat):
        return True

    return False