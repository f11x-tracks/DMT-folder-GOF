import os
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

# Test with the example XML file to understand the data structure
file_path = r'c:\Users\strautma\PythonScripts\DMT-folder-GOF\2025-07-08T09.33.59.9790672-W525T8V0-8333-DMT102-TNI111-5051IN009THK.xml'

records = []

tree = ET.parse(file_path)
root = tree.getroot()

# Look at the first few DataRecord elements to understand the structure
data_records = root.findall('.//DataRecord')[:20]

for i, record in enumerate(data_records):
    label = record.findtext('Label')
    datum = record.findtext('Datum')
    wafer_id = record.findtext('WaferID')
    sindex = record.findtext('SIndex')
    print(f"Record {i}: SIndex={sindex}, WaferID={wafer_id}, Label={label}, Datum={datum}")
