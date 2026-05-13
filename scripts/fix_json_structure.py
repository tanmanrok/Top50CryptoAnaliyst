import json
from datetime import datetime

# Read current predictions
with open('data/validation/predictions_7day.json', 'r') as f:
    data = json.load(f)

# Rebuild with proper structure
validation_data = {
    "start_date": "2026-05-09T20:15:45.423978",
    "end_date": None,
    "predictions": data.get('predictions', [])
}

# Write back
with open('data/validation/predictions_7day.json', 'w') as f:
    json.dump(validation_data, f, indent=2)

print("✅ Fixed JSON structure with metadata fields")
