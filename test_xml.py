import os
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

# Test XML parsing
file_path = r'c:\Users\strautma\PythonScripts\DMT-folder-GOF\2025-07-08T09.33.59.9790672-W525T8V0-8333-DMT102-TNI111-5051IN009THK.xml'

print(f"Testing XML file: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

records = []

try:
    # Get file datetime (last modified)
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    print(f"File timestamp: {file_time}")
    
    # Parse XML
    tree = ET.parse(file_path)
    root = tree.getroot()
    print(f"Root element: {root.tag}")
    
    # Looking for DataRecord elements with Label and Datum children
    data_records = root.findall('.//DataRecord')
    print(f"Found {len(data_records)} DataRecord elements")
    
    for data_record in data_records:
        label = data_record.findtext('Label')
        datum = data_record.findtext('Datum')
        if label in ['Layer 1 Thickness', 'Goodness-of-Fit']:
            try:
                datum_val = float(datum)
                records.append({
                    'datetime': file_time,
                    'Label': label,
                    'Datum': datum_val
                })
                print(f"Found: {label} = {datum_val}")
            except (TypeError, ValueError) as e:
                print(f"Error converting {label}: {datum} - {e}")
                continue
                
except Exception as e:
    print(f"Error processing file: {e}")

print(f"\nTotal records extracted: {len(records)}")

if records:
    df = pd.DataFrame(records)
    print("\nDataFrame summary:")
    print(df.groupby('Label').agg({'Datum': ['count', 'mean', 'min', 'max']}))
else:
    print("No data extracted!")
