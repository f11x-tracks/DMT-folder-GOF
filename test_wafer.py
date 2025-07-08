import os
import glob
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

# Test with the example XML file
file_path = r'c:\Users\strautma\PythonScripts\DMT-folder-GOF\2025-07-08T09.33.59.9790672-W525T8V0-8333-DMT102-TNI111-5051IN009THK.xml'

records = []

try:
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    dmt = 'DMT102'  # Since this is from our example
    
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
print(f"Total records: {len(records)}")
print(f"Unique WaferIDs: {df['WaferID'].nunique()}")
print(f"WaferIDs found: {sorted(df['WaferID'].unique())}")
print(f"\nSample data:")
print(df.head(10))
