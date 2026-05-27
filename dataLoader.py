import pandas as pd
from copy import deepcopy

path = "../dataset_modeling.csv"

def retrieve_data(path:str):
    with open(path) as f:
        file = pd.read_csv(f)
    df = deepcopy(file)

    file.insert(0, 'id', range(len(file)))

    columns = file.keys()
    raw_data = [tuple(item) for item in file.values]
    return columns, raw_data, df

if __name__ == "__main__":
    columns, raw_data, _ = retrieve_data(path)
    print(columns)







