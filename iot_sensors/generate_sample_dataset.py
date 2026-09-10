"""
Generate a sample Bangalore traffic dataset for testing
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Bangalore locations (matching the simulator)
locations = [
    "MG Road",
    "Hosur Road",
    "Indiranagar 100ft Road",
    "Outer Ring Road",
    "Jayanagar 4th Block",
    "Bellary Road",
    "Koramangala 80ft Road",
    "Bannerghatta Road"
]

# Generate sample data for one week
start_date = datetime(2024, 11, 1, 0, 0, 0)
records = []

# Generate data every 15 minutes for 7 days
for day in range(7):
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            timestamp = start_date + timedelta(days=day, hours=hour, minutes=minute)
            
            for location in locations:
                # Simulate traffic patterns
                is_peak = hour in [7, 8, 9, 17, 18, 19]
                is_weekend = day >= 5
                
                # Base traffic volume
                if is_peak and not is_weekend:
                    base_volume = np.random.randint(800, 1500)
                    congestion = np.random.choice([3, 4, 5], p=[0.3, 0.4, 0.3])
                    speed = np.random.randint(15, 35)
                elif hour in [10, 11, 12, 13, 14, 15, 16]:
                    base_volume = np.random.randint(400, 800)
                    congestion = np.random.choice([2, 3], p=[0.6, 0.4])
                    speed = np.random.randint(30, 50)
                else:
                    base_volume = np.random.randint(100, 400)
                    congestion = np.random.choice([1, 2], p=[0.7, 0.3])
                    speed = np.random.randint(40, 60)
                
                # Weekend adjustment
                if is_weekend:
                    base_volume = int(base_volume * 0.7)
                    congestion = max(1, congestion - 1)
                    speed = min(60, speed + 10)
                
                records.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'location': location,
                    'traffic_volume': base_volume,
                    'average_speed': speed,
                    'congestion_level': congestion
                })

# Create DataFrame
df = pd.DataFrame(records)

# Save to CSV
import os
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'bangalore_traffic.csv')
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} records")
print(f"Saved to: {output_path}")
print(f"\nDataset info:")
print(df.info())
print(f"\nSample data:")
print(df.head(10))
print(f"\nCongestion level distribution:")
print(df['congestion_level'].value_counts().sort_index())

