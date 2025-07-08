import os
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

# Test the updated data extraction
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
            
            records.append({
                'datetime': file_time,
                'Label': label,
                'Datum': datum_val,
                'dmt': dmt,
                'WaferID': wafer_id,
                'XWaferLoc': x_wafer_loc,
                'YWaferLoc': y_wafer_loc,
                'location_id': location_id
            })
        except (TypeError, ValueError):
            continue

df = pd.DataFrame(records)

print(f"Total records: {len(records)}")
print(f"Records with location_id: {df['location_id'].notna().sum()}")
print(f"Unique locations: {df['location_id'].nunique()}")

# Test scatter plot data
df_with_location = df[df['location_id'].notna()].copy()
gof_data = df_with_location[df_with_location['Label'] == 'Goodness-of-Fit'][['datetime', 'WaferID', 'dmt', 'location_id', 'Datum']].rename(columns={'Datum': 'GoodnessOfFit'})
thickness_data = df_with_location[df_with_location['Label'] == 'Layer 1 Thickness'][['datetime', 'WaferID', 'dmt', 'location_id', 'Datum']].rename(columns={'Datum': 'Layer1Thickness'})

merged_data = pd.merge(gof_data, thickness_data, on=['datetime', 'WaferID', 'dmt', 'location_id'], how='inner')

print(f"GoF records with location: {len(gof_data)}")
print(f"Thickness records with location: {len(thickness_data)}")
print(f"Merged scatter plot data: {len(merged_data)}")
print("\nSample merged data:")
print(merged_data.head())
