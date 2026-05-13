import json
from datetime import datetime

# Read the JSON file
with open('data/validation/predictions_7day.json', 'r') as f:
    data = json.load(f)

# Remove duplicates by target_date, keeping only the first occurrence
seen_dates = {}
unique_predictions = []

for pred in data['predictions']:
    target_date = pred['target_date']
    if target_date not in seen_dates:
        seen_dates[target_date] = True
        unique_predictions.append(pred)

# Re-number days
for i, pred in enumerate(unique_predictions, 1):
    pred['day'] = i

# Write back
with open('data/validation/predictions_7day.json', 'w') as f:
    json.dump({'predictions': unique_predictions}, f, indent=2)

print(f"✅ Cleaned JSON: {len(data['predictions'])} → {len(unique_predictions)} predictions")
print(f"Unique target dates: {sorted(set(p['target_date'] for p in unique_predictions))}")
