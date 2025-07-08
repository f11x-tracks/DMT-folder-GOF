import os
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import numpy as np

# Test RADIUS calculation
file_path = r'c:\Users\strautma\PythonScripts\DMT-folder-GOF\2025-07-08T09.33.59.9790672-W525T8V0-8333-DMT102-TNI111-5051IN009THK.xml'

records = []

file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
dmt = 'DMT102'

tree = ET.parse(file_path)
root = tree.getroot()

for data_record in root.findall('.//DataRecord'):
    label = data_record.findtext('Label')
    datum = data_record.findtext('Datum')
    wafer_id = data_record.findtext('WaferID')
    x_wafer_loc = data_record.findtext('XWaferLoc')
    y_wafer_loc = data_record.findtext('YWaferLoc')
    
    if label in ['Layer 1 Thickness', 'Goodness-of-Fit']:
        try:
            datum_val = float(datum)
            location_id = f"{x_wafer_loc}_{y_wafer_loc}" if x_wafer_loc and y_wafer_loc else None
            
            # Calculate RADIUS
            radius = None
            if x_wafer_loc and y_wafer_loc:
                try:
                    x_val = float(x_wafer_loc)
                    y_val = float(y_wafer_loc)
                    radius = np.sqrt(x_val**2 + y_val**2)
                except (ValueError, TypeError):
                    radius = None
            
            records.append({
                'datetime': file_time,
                'Label': label,
                'Datum': datum_val,
                'dmt': dmt,
                'WaferID': wafer_id,
                'XWaferLoc': x_wafer_loc,
                'YWaferLoc': y_wafer_loc,
                'location_id': location_id,
                'RADIUS': radius
            })
        except (TypeError, ValueError):
            continue

df = pd.DataFrame(records)

print(f"Total records: {len(records)}")
print(f"Records with RADIUS: {df['RADIUS'].notna().sum()}")
print(f"RADIUS range: {df['RADIUS'].min():.2f} to {df['RADIUS'].max():.2f}")

# Check Layer 1 Thickness data with RADIUS
thickness_data = df[(df['Label'] == 'Layer 1 Thickness') & (df['RADIUS'].notna())].copy()
print(f"Layer 1 Thickness records with RADIUS: {len(thickness_data)}")
print(f"Unique WaferIDs: {thickness_data['WaferID'].nunique()}")
print(f"WaferIDs: {sorted(thickness_data['WaferID'].unique())}")

print("\nSample data with RADIUS:")
print(thickness_data[['WaferID', 'XWaferLoc', 'YWaferLoc', 'RADIUS', 'Datum']].head(10))
