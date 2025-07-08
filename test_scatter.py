import os
import glob
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import plotly.express as px

# Test with the example XML file
file_path = r'c:\Users\strautma\PythonScripts\DMT-folder-GOF\2025-07-08T09.33.59.9790672-W525T8V0-8333-DMT102-TNI111-5051IN009THK.xml'

records = []

try:
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    dmt = 'DMT102'
    
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for data_record in root.findall('.//DataRecord'):
        label = data_record.findtext('Label')
        datum = data_record.findtext('Datum')
        wafer_id = data_record.findtext('WaferID')
        if label in ['Layer 1 Thickness', 'Goodness-of-Fit']:
            try:
                datum_val = float(datum)
                records.append({
                    'datetime': file_time,
                    'Label': label,
                    'Datum': datum_val,
                    'dmt': dmt,
                    'WaferID': wafer_id
                })
            except (TypeError, ValueError):
                continue
                
except Exception as e:
    print(f"Error: {e}")

df = pd.DataFrame(records)

# Test scatter plot data preparation with measurement_id
df_with_index = df.copy()
df_with_index['measurement_id'] = df_with_index.groupby(['datetime', 'WaferID', 'dmt']).cumcount()

gof_data = df_with_index[df_with_index['Label'] == 'Goodness-of-Fit'][['datetime', 'WaferID', 'dmt', 'measurement_id', 'Datum']].rename(columns={'Datum': 'GoodnessOfFit'})
thickness_data = df_with_index[df_with_index['Label'] == 'Layer 1 Thickness'][['datetime', 'WaferID', 'dmt', 'measurement_id', 'Datum']].rename(columns={'Datum': 'Layer1Thickness'})

merged_data = pd.merge(gof_data, thickness_data, on=['datetime', 'WaferID', 'dmt', 'measurement_id'], how='inner')

print(f"Original records: {len(records)}")
print(f"GoF records: {len(gof_data)}")
print(f"Thickness records: {len(thickness_data)}")
print(f"Merged records: {len(merged_data)}")
print(f"Unique WaferIDs in merged data: {merged_data['WaferID'].nunique()}")
print("\nSample merged data:")
print(merged_data.head(10))
