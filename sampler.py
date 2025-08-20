# create a sample of the dataset data/dados.csv 
import pandas as pd

df = pd.read_csv("data/dados.csv")
sample = df.sample(frac=0.01, random_state=42)
sample.to_csv("data/dados_sample.csv", index=False)
print("Sample created and saved to data/dados_sample.csv")
print(f"Sample size: {len(sample)} rows")
print(f"Original dataset size: {len(df)} rows")
print("Sampled data preview:")
print(sample.head())
print("Sampling completed successfully.")