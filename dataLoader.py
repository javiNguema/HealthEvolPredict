import pandas as pd
from copy import deepcopy
from typing import Tuple, List



def retrieve_data(path: str, precision: int = 4) -> Tuple[pd.Index, list, pd.DataFrame]:
    with open(path) as f:
        file = pd.read_csv(f)
    df = deepcopy(file)

    file.insert(0, 'id', range(len(file)))
    columns = file.keys()
    
    # Formats floats to the specified precision as strings, leaves other types as-is
    raw_data = [
        tuple(f"{item:.{precision}f}" if isinstance(item, float) else item for item in row)
        for row in file.values
    ]
    
    return columns, raw_data, df






