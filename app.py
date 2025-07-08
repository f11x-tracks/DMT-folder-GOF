import os
import glob
import pandas as pd
from datetime import datetime
import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy import stats

import xml.etree.ElementTree as ET

import plotly.express as px
import plotly.graph_objects as go

# Directories to search
dirs = [r'Y:\Xfile\DMT102', r'Y:\Xfile\DMT103']
patterns = ['*W525T8V0-8333-DMT103-TDJ591-DMTDUMMY.xml', '*5051IN009THK*.xml']

# Get all files
files = []
for d in dirs:
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(d, pattern)))

print(f"Found {len(files)} XML files to process")

# Collect data
records = []
processed_files = []  # Track successfully processed files

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
        
        # Add to processed files list if we got here without errors
        processed_files.append({
            'filename': os.path.basename(file),
            'full_path': file,
            'dmt_type': dmt,
            'file_datetime': file_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
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

def make_radius_thickness_plots():
    # Filter for Layer 1 Thickness data with valid RADIUS
    thickness_data = df[(df['Label'] == 'Layer 1 Thickness') & (df['RADIUS'].notna())].copy()
    
    if thickness_data.empty:
        return html.Div("No Layer 1 Thickness data with RADIUS available")
    
    unique_wafers = sorted(thickness_data['WaferID'].unique())
    plots = []
    
    for wafer_id in unique_wafers:
        wafer_data = thickness_data[thickness_data['WaferID'] == wafer_id].copy()
        
        if wafer_data.empty or len(wafer_data) < 3:
            continue
            
        # Create scatter plot
        fig = go.Figure()
        
        # Add scatter points colored by DMT type
        for dmt_type in wafer_data['dmt'].unique():
            dmt_data = wafer_data[wafer_data['dmt'] == dmt_type]
            fig.add_trace(go.Scatter(
                x=dmt_data['RADIUS'],
                y=dmt_data['Datum'],
                mode='markers',
                name=f'{dmt_type}',
                marker=dict(size=8),
                text=dmt_data['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                              'RADIUS: %{x:.2f}<br>' +
                              'Thickness: %{y:.2f}<br>' +
                              'DateTime: %{text}<br>' +
                              '<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=f'Layer 1 Thickness vs RADIUS - WaferID: {wafer_id}',
            xaxis_title='RADIUS',
            yaxis_title='Layer 1 Thickness',
            xaxis=dict(range=[0, 150]),
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=True
        )
        
        plots.append(dcc.Graph(figure=fig))
    
    return html.Div(plots)

def make_files_table():
    """Create a table showing all processed XML files"""
    if not processed_files:
        return html.Div("No files were processed")
    
    # Create a DataFrame for the table
    files_df = pd.DataFrame(processed_files)
    
    # Create the table using dash_table
    table = dash_table.DataTable(
        data=files_df.to_dict('records'),
        columns=[
            {"name": "File Name", "id": "filename"},
            {"name": "DMT Type", "id": "dmt_type"},
            {"name": "File Date/Time", "id": "file_datetime"},
            {"name": "Full Path", "id": "full_path"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{dmt_type} = DMT102'},
                'backgroundColor': 'rgba(255, 182, 193, 0.3)',
            },
            {
                'if': {'filter_query': '{dmt_type} = DMT103'},
                'backgroundColor': 'rgba(173, 216, 230, 0.3)',
            }
        ],
        page_size=20,
        sort_action="native",
        filter_action="native"
    )
    
    return html.Div([
        html.H3(f"Processed XML Files ({len(processed_files)} total)"),
        table
    ])

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
    
    html.H2("Layer 1 Thickness vs RADIUS by WaferID"),
    make_radius_thickness_plots(),
    
    html.Hr(),
    
    html.H2("Layer 1 Thickness by WaferID"),
    make_wafer_plots('Layer 1 Thickness'),
    
    html.H2("Goodness-of-Fit by WaferID"),
    make_wafer_plots('Goodness-of-Fit'),
    
    html.Hr(),
    
    html.H2("Processed XML Files"),
    make_files_table()
])

if __name__ == '__main__':
    app.run_server(debug=True)