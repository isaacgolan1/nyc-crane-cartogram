import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('Centerline_20260828.csv')

# Borough names
borough_names = {
    1: 'Manhattan',
    2: 'Bronx',
    3: 'Brooklyn',
    4: 'Queens',
    5: 'Staten Island'
}

# Get average width by borough
borough_stats = df.groupby('Borough Code')['Street Width'].mean().sort_values(ascending=False)

# Rename with borough names
borough_stats.index = [borough_names[code] for code in borough_stats.index]

# Create bar chart
plt.figure(figsize=(10, 6))
borough_stats.plot(kind='bar', color='steelblue', edgecolor='black')
plt.title('Average Street Width by NYC Borough', fontsize=14, fontweight='bold')
plt.xlabel('Borough', fontsize=12)
plt.ylabel('Average Street Width (feet)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Save the chart
plt.savefig('street_width_by_borough.png', dpi=150)
print("Chart saved as 'street_width_by_borough.png'")

# Get median width by borough
borough_median = df.groupby('Borough Code')['Street Width'].median().sort_values(ascending=False)
borough_median.index = [borough_names[code] for code in borough_median.index]

# Create second chart for median
plt.figure(figsize=(10, 6))
borough_median.plot(kind='bar', color='coral', edgecolor='black')
plt.title('Median Street Width by NYC Borough', fontsize=14, fontweight='bold')
plt.xlabel('Borough', fontsize=12)
plt.ylabel('Median Street Width (feet)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Save the chart
plt.savefig('street_width_median_by_borough.png', dpi=150)
print("Median chart saved as 'street_width_median_by_borough.png'")

# Relationship between number of travel lanes and street width
lanes_df = df[(df['Number Travel Lanes'] > 0) & (df['Number Travel Lanes'] <= 6)]
correlation = lanes_df['Number Travel Lanes'].corr(lanes_df['Street Width'])

plt.figure(figsize=(10, 6))
lanes_df.boxplot(column='Street Width', by='Number Travel Lanes', grid=False)
plt.suptitle('')
plt.title(f'Street Width by Number of Travel Lanes (r = {correlation:.2f})', fontsize=14, fontweight='bold')
plt.xlabel('Number of Travel Lanes', fontsize=12)
plt.ylabel('Street Width (feet)', fontsize=12)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Save the chart
plt.savefig('street_width_by_lanes.png', dpi=150)
print(f"Lanes chart saved as 'street_width_by_lanes.png' (correlation r = {correlation:.2f})")
plt.show()