import os
import glob
import pandas as pd
from datetime import datetime
import dash
from dash import dcc, html

import xml.etree.ElementTree as ET

import plotly.express as px

# Directories to search
dirs = [r'Y:\Xfile\DMT102', r'Y:\Xfile\DMT103']
pattern = '*5051IN009THK*.xml'

# Get all files
files = []
for d in dirs:
    files.extend(glob.glob(os.path.join(d, pattern)))

# Collect data
records = []

for file in files:
    try:
        # Get file datetime (last modified)
        file_time = datetime.fromtimestamp(os.path.getmtime(file))
        
        # Determine DMT type from file path
        if 'DMT102' in file:
            dmt = 'DMT102'
        elif 'DMT103' in file:
            dmt = 'DMT103'
        else:
            dmt = 'Unknown'
            
        # Parse XML
        tree = ET.parse(file)
        root = tree.getroot()
        # Looking for DataRecord elements with Label and Datum children
        for data_record in root.findall('.//DataRecord'):
            label = data_record.findtext('Label')
            datum = data_record.findtext('Datum')
            wafer_id = data_record.findtext('WaferID')
            x_wafer_loc = data_record.findtext('XWaferLoc')
            y_wafer_loc = data_record.findtext('YWaferLoc')
            
            if label in ['Layer 1 Thickness', 'Goodness-of-Fit']:
                try:
                    datum_val = float(datum)
                    # Create a unique location identifier for pairing measurements
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
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        continue

df = pd.DataFrame(records)

# Dash app
app = dash.Dash(__name__)

def make_boxplot(label):
    dff = df[df['Label'] == label]
    if dff.empty:
        return html.Div(f"No data for {label}")
    fig = px.box(
        dff,
        x=dff['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S'),
        y='Datum',
        color='dmt',
        points='all',
        title=f'Boxplot of {label} over Time',
        labels={'Datum': label, 'datetime': 'File DateTime', 'dmt': 'DMT Type'}
    )
    fig.update_layout(xaxis_title='File DateTime', yaxis_title=label)
    return dcc.Graph(figure=fig)

def make_wafer_plots(label):
    dff = df[df['Label'] == label]
    if dff.empty:
        return html.Div(f"No data for {label}")
    
    unique_wafers = sorted(dff['WaferID'].unique())
    plots = []
    
    for wafer_id in unique_wafers:
        wafer_data = dff[dff['WaferID'] == wafer_id]
        if not wafer_data.empty:
            fig = px.box(
                wafer_data,
                x=wafer_data['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                y='Datum',
                color='dmt',
                points='all',
                title=f'{label} - WaferID: {wafer_id}',
                labels={'Datum': label, 'datetime': 'File DateTime', 'dmt': 'DMT Type'}
            )
            fig.update_layout(
                xaxis_title='File DateTime', 
                yaxis_title=label,
                height=400,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            plots.append(dcc.Graph(figure=fig))
    
    return html.Div(plots)

def make_scatter_plot():
    # Filter data that has location information for proper pairing
    df_with_location = df[df['location_id'].notna()].copy()
    
    if df_with_location.empty:
        return html.Div("No location data available for scatter plot")
    
    # Separate GoF and Thickness data
    gof_data = df_with_location[df_with_location['Label'] == 'Goodness-of-Fit'][['datetime', 'WaferID', 'dmt', 'location_id', 'Datum']].rename(columns={'Datum': 'GoodnessOfFit'})
    thickness_data = df_with_location[df_with_location['Label'] == 'Layer 1 Thickness'][['datetime', 'WaferID', 'dmt', 'location_id', 'Datum']].rename(columns={'Datum': 'Layer1Thickness'})
    
    # Merge based on location (same measurement point)
    merged_data = pd.merge(gof_data, thickness_data, on=['datetime', 'WaferID', 'dmt', 'location_id'], how='inner')
    
    if merged_data.empty:
        return html.Div("No paired measurement data available for scatter plot")
    
    fig = px.scatter(
        merged_data,
        x='GoodnessOfFit',
        y='Layer1Thickness',
        color='dmt',
        symbol='WaferID',
        title='Layer 1 Thickness vs Goodness-of-Fit (Same Measurement Points)',
        labels={
            'GoodnessOfFit': 'Goodness-of-Fit',
            'Layer1Thickness': 'Layer 1 Thickness',
            'dmt': 'DMT Type'
        },
        hover_data=['WaferID', 'datetime']
    )
    
    fig.update_layout(
        xaxis_title='Goodness-of-Fit',
        yaxis_title='Layer 1 Thickness',
        height=600,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return dcc.Graph(figure=fig)

app.layout = html.Div([
    html.H1("XML Data Analysis"),
    
    html.H2("Overall Data - Layer 1 Thickness"),
    make_boxplot('Layer 1 Thickness'),
    
    html.H2("Overall Data - Goodness-of-Fit"),
    make_boxplot('Goodness-of-Fit'),
    
    html.Hr(),
    
    html.H2("Layer 1 Thickness vs Goodness-of-Fit Correlation"),
    make_scatter_plot(),
    
    html.Hr(),
    
    html.H2("Layer 1 Thickness by WaferID"),
    make_wafer_plots('Layer 1 Thickness'),
    
    html.H2("Goodness-of-Fit by WaferID"),
    make_wafer_plots('Goodness-of-Fit')
])

if __name__ == '__main__':
    app.run_server(debug=True)