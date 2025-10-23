import pandas as pd

# Read the CSV files with UTF-8 encoding
df = pd.read_csv("input_data/pubs-2022-utf-8.csv", encoding="utf-8")

unique_types = set()
for types in df["Article Type"].dropna():
    for t in types.split(","):
        unique_types.add(t.strip())

print(unique_types)
