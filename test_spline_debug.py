import os
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import numpy as np
from scipy.interpolate import UnivariateSpline
import plotly.graph_objects as go

# Test spline fitting with the example data
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
    
    if label in ['Layer 1 Thickness']:
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
thickness_data = df[(df['Label'] == 'Layer 1 Thickness') & (df['RADIUS'].notna())].copy()

print(f"Total thickness records with RADIUS: {len(thickness_data)}")
print(f"Unique WaferIDs: {thickness_data['WaferID'].nunique()}")

# Test spline fitting for first wafer
wafer_id = thickness_data['WaferID'].iloc[0]
wafer_data = thickness_data[thickness_data['WaferID'] == wafer_id].copy()

print(f"\nTesting spline for WaferID: {wafer_id}")
print(f"Data points for this wafer: {len(wafer_data)}")

if len(wafer_data) >= 4:
    try:
        # Sort data by RADIUS
        sorted_data = wafer_data.sort_values('RADIUS')
        x_data = sorted_data['RADIUS'].values
        y_data = sorted_data['Datum'].values
        
        print(f"X data range: {x_data.min():.2f} to {x_data.max():.2f}")
        print(f"Y data range: {y_data.min():.2f} to {y_data.max():.2f}")
        
        # Try different smoothing factors
        for s_factor in [None, 0, len(x_data) * 0.1, len(x_data) * 1.0]:
            try:
                spline = UnivariateSpline(x_data, y_data, s=s_factor, k=min(3, len(x_data)-1))
                
                # Test curve generation
                x_curve = np.linspace(0, 150, 50)
                y_curve = spline(x_curve)
                
                print(f"Smoothing factor {s_factor}: SUCCESS")
                print(f"  Curve Y range: {y_curve.min():.2f} to {y_curve.max():.2f}")
                
                # Test if any values are reasonable
                data_y_range = y_data.max() - y_data.min()
                curve_y_range = y_curve.max() - y_curve.min()
                print(f"  Data Y range: {data_y_range:.2f}, Curve Y range: {curve_y_range:.2f}")
                
                break
                
            except Exception as e:
                print(f"Smoothing factor {s_factor}: FAILED - {e}")
                
    except Exception as e:
        print(f"Overall spline fitting failed: {e}")
else:
    print("Not enough data points for spline fitting")
