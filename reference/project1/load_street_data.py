import pandas as pd

# Load the street data from the CSV file
print("Loading NYC street data...")

df = pd.read_csv('Centerline_20260828.csv')

print("Data loaded!")
print(f"\nTotal records: {len(df)}")
print(f"\nColumn names:")
print(df.columns.tolist())
print("\n" + "="*80)
print("First few rows:")
print(df.head())
print("\n" + "="*80)
print("\nData shape (rows, columns):", df.shape)