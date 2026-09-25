import pandas as pd

# Load the data
df = pd.read_csv('Centerline_20260828.csv')

print("="*80)
print("NYC STREET WIDTH ANALYSIS")
print("="*80)

# Check all borough-related columns
print("\nBorough-related columns:")
print(f"Borough Indicator unique values: {df['Borough Indicator'].unique()}")
print(f"Borough Code unique values: {df['Borough Code'].unique()}")

# Look at a sample row to see what we're working with
print("\n" + "="*80)
print("Sample row (full info):")
print("="*80)
print(df.iloc[0][['STREET NAME', 'Street Width', 'Borough Indicator', 'Borough Code']])

# Try grouping by Borough Code instead
print("\n" + "="*80)
print("AVERAGE STREET WIDTH BY BOROUGH CODE:")
print("="*80)
borough_stats = df.groupby('Borough Code')['Street Width'].agg(['mean', 'median', 'count', 'min', 'max'])
print(borough_stats)

# Also just overall stats
print("\n" + "="*80)
print("OVERALL STATISTICS:")
print("="*80)
print(f"Average street width: {df['Street Width'].mean():.2f} feet")
print(f"Median street width: {df['Street Width'].median():.2f} feet")
print(f"Narrowest street: {df['Street Width'].min():.2f} feet")
print(f"Widest street: {df['Street Width'].max():.2f} feet")
print(f"Standard deviation: {df['Street Width'].std():.2f} feet")