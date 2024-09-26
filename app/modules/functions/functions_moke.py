"""
Functions used in MOKE interactive plot using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import numpy as np
import plotly.graph_objects as go
import pandas as pd
from scipy.signal import savgol_filter
from collections import defaultdict
import re


def get_pulse_voltage(folderpath):
    infopath = folderpath / 'info.txt'
    try:
        with open(infopath, "r", encoding="iso-8859-1") as file_info:
            for line in file_info:
                if "Pulse_voltage" in line:
                    pulse_volt = line.split("=")[1]
        return int(pulse_volt)
    except FileNotFoundError:
        return None

def get_measurement_count(folderpath):
    infopath = folderpath / 'info.txt'
    try:
        with open(infopath, "r", encoding="iso-8859-1") as file_info:
            for line in file_info:
                if "Average_per_point" in line:
                    avg_pts = line.split("=")[1]
        return int(avg_pts)
    except FileNotFoundError:
        return None

def load_measurement_files(folderpath, target_x, target_y, measurement_id):
    files = []
    for path in folderpath.glob('p*.txt'):
        file_x = float(path.name.split('_')[1].lstrip('x'))
        file_y = float(path.name.split('_')[2].lstrip('y'))
        if file_x == target_x and file_y == target_y:
            files.append(path)
    for path in files:
        if 'magnetization' in str(path):
            mag = pd.read_table(path).dropna(axis=1, how='all')
        elif 'pulse' in str(path):
            pulse = pd.read_table(path).dropna(axis=1, how='all')
        elif 'sum' in str(path):
            sum = pd.read_table(path).dropna(axis=1, how='all')

    if measurement_id == 0:
        data = pd.DataFrame({'Magnetization': mag.mean(axis=1),
                             'Pulse': pulse.mean(axis=1),
                             'Sum': sum.mean(axis=1)
                             })
        return data

    elif measurement_id > 0:
        idx = measurement_id-1
        data = pd.DataFrame({'Magnetization': mag.iloc[:, idx],
                             'Pulse': pulse.iloc[:, idx],
                             'Sum': sum.iloc[:, idx]
                             })
        return data

    else:
        raise ValueError('Measurement number invalid, either out of range or not an integer')



def calculate_loop_from_data(data, pulse_voltage, coil_factor=0.92667):
    max_field = coil_factor * pulse_voltage
    # Remove pulse noise to isolate actual pulse signal
    data['Pulse'] = data['Pulse'].replace(0.0016667, 0)
    data['Pulse'] = data['Pulse'].replace(-0.0016667, 0)
    # Integrate pulse during triggers to get field
    data.loc[330:670, 'Field'] = data.loc[330:670, 'Pulse'].cumsum()
    data.loc[1330:1670, 'Field'] = data.loc[1330:1670, 'Pulse'].cumsum()
    # Correct field with coil parameters
    midpoint = len(data) // 2
    data.loc[:midpoint, 'Field'] = data.loc[:midpoint, 'Field'].apply(
        lambda x: -x * max_field / np.abs(data['Field'].min()))
    data.loc[midpoint:, 'Field'] = data.loc[midpoint:, 'Field'].apply(
        lambda x: -x * max_field / np.abs(data['Field'].max()))

    # Correct Magnetization for Oscilloscope offset
    offset = data['Magnetization'].mean()
    data['Magnetization'] = data['Magnetization'].apply(lambda x: x - offset)
    data['Magnetization'] = savgol_filter(data['Magnetization'], 41, 3)

    non_nan = data[data['Field'].notna()].index.values
    section = data.loc[non_nan, ('Magnetization', 'Field', 'Sum')]
    section.reset_index(drop=True, inplace=True)
    return section


def get_kerr_rotation(folderpath, target_x, target_y):
    data = load_measurement_files(folderpath, target_x, target_y, measurement_id=0)
    offset = data['Magnetization'].mean()
    data['Magnetization'] = data['Magnetization'].apply(lambda x: x - offset)
    data['Magnetization'] = savgol_filter(data['Magnetization'], 41, 3)
    kerr_max = data['Magnetization'].max()
    kerr_min = data['Magnetization'].min()
    kerr_mean = (kerr_max + np.abs(kerr_min) )/2
    return kerr_mean


def get_reflectivity(folderpath, target_x, target_y):
    for path in folderpath.glob('*_sum.txt'):
        file_x = float(path.name.split('_')[1].lstrip('x'))
        file_y = float(path.name.split('_')[2].lstrip('y'))
        if file_x == target_x and file_y == target_y:
            sum = pd.read_table(path)
            reflectivity = sum.mean(axis=0)
            if type(reflectivity) is pd.Series:
                reflectivity = reflectivity.mean()
            return reflectivity


def get_derivative_coercivity(folderpath, target_x, target_y, mean=True):
    pulse_voltage = get_pulse_voltage(folderpath) / 100
    data = load_measurement_files(folderpath, target_x, target_y, measurement_id=0)
    data = calculate_loop_from_data(data, pulse_voltage, coil_factor=0.92667)
    data['Derivative'] = data['Magnetization'] - data['Magnetization'].shift(1)
    data.loc[np.abs(data['Field']) < 1e-3, 'Derivative'] = 0 # Avoid derivative discrepancies around 0 Field
    # For positive / negative field, find index of maximum / minimum derivative and extract corresponding field
    coercivity_positive = data.loc[data.loc[data['Field'] > 0, 'Derivative'].idxmax(), 'Field']
    coercivity_negative = data.loc[data.loc[data['Field'] < 0, 'Derivative'].idxmin(), 'Field']
    if mean == True:
        coercivity = (np.abs(coercivity_positive) + np.abs(coercivity_negative)) / 2
        return coercivity
    else:
        return coercivity_positive, coercivity_negative


def get_measured_coercivity(folderpath, target_x, target_y, mean=True):
    pulse_voltage = get_pulse_voltage(folderpath) / 100
    data = load_measurement_files(folderpath, target_x, target_y, measurement_id=0)
    data = calculate_loop_from_data(data, pulse_voltage, coil_factor=0.92667)
    coercivity_positive = data.loc[np.abs(data.loc[data['Field'] > 0, 'Magnetization']).idxmin(), 'Field']
    coercivity_negative = data.loc[np.abs(data.loc[data['Field'] < 0, 'Magnetization']).idxmin(), 'Field']
    if mean == True:
        coercivity = (np.abs(coercivity_positive) + np.abs(coercivity_negative)) / 2
        return coercivity
    else:
        return coercivity_positive, coercivity_negative


def make_database(folderpath, coil_factor=0.92667):
    pulse_voltage = get_pulse_voltage(folderpath) / 100

    # Regular expression to match 'p' followed by a number
    pattern = re.compile(r'p(\d+)')

    grouped_files = defaultdict(list)

    # Use glob to iterate through the files and group them by p-number
    for filepath in folderpath.glob('p*.txt'):
        match = pattern.search(filepath.name)
        if match:
            number = match.group(1)  # Extract the p-number
            grouped_files[number].append(filepath)

    database = pd.DataFrame()
    # Now filter out groups that don't have exactly 3 files
    for number, files in grouped_files.items():
        i = int(number) - 1
        for path in files:
            if 'magnetization' in str(path):
                mag = pd.read_table(path).dropna(axis=1, how='all')
            elif 'pulse' in str(path):
                pulse = pd.read_table(path).dropna(axis=1, how='all')
            elif 'sum' in str(path):
                sum = pd.read_table(path).dropna(axis=1, how='all')

        data = pd.DataFrame({'Magnetization': mag.mean(axis=1),
                             'Pulse': pulse.mean(axis=1),
                             'Sum': sum.mean(axis=1)
                             })

        data = calculate_loop_from_data(data, pulse_voltage, coil_factor)

        # Get Kerr rotation
        kerr_max = data['Magnetization'].max()
        kerr_min = data['Magnetization'].min()
        kerr_mean = (kerr_max + np.abs(kerr_min)) / 2

        # Get reflectivity
        reflectivity = data['Sum'].mean(axis=0)
        if type(reflectivity) is pd.Series:
            reflectivity = reflectivity.mean()

        # Get coercivity from derivative
        data['Derivative'] = data['Magnetization'] - data['Magnetization'].shift(1)
        data.loc[np.abs(data['Field']) < 1e-3, 'Derivative'] = 0  # Avoid derivative discrepancies around 0 Field
        coercivity_positive = data.loc[data['Derivative'].idxmax(), 'Field']
        coercivity_negative = data.loc[data['Derivative'].idxmin(), 'Field']
        d_coercivity = (np.abs(coercivity_positive) + np.abs(coercivity_negative)) / 2

        # Get coercivity from measurement
        coercivity_positive = data.loc[np.abs(data.loc[data['Field'] > 0, 'Magnetization']).idxmin(), 'Field']
        coercivity_negative = data.loc[np.abs(data.loc[data['Field'] < 0, 'Magnetization']).idxmin(), 'Field']
        m_coercivity = (np.abs(coercivity_positive) + np.abs(coercivity_negative)) / 2

        # Assign to database
        database.loc[i, 'File Number'] = number
        database.loc[i, 'x_pos (mm)'] = float(path.name.split('_')[1].lstrip('x'))
        database.loc[i, 'y_pos (mm)'] = float(path.name.split('_')[2].lstrip('y'))
        database.loc[i, 'Kerr Rotation (deg)'] = kerr_mean
        database.loc[i, 'Reflectivity (V)'] = reflectivity
        database.loc[i, 'Derivative Coercivity (T)'] = d_coercivity
        database.loc[i, 'Measured Coercivity (T)'] = m_coercivity

    database_path = folderpath / 'database.csv'
    database.to_csv(database_path, index=False)
    return database_path


def heatmap_plot(folderpath, mode, title=''):
    database = pd.read_csv(folderpath / 'database.csv')

    # Plot parameters
    layout = go.Layout(
        title=title,
        xaxis=dict(range=[-50, 50], title='X (mm)'),
        yaxis=dict(range=[-50, 50], title='Y (mm)'),
        height=700,
        width=700
    )

    # Exit if no database is found
    if database is None:
        return go.Figure(layout=layout)

    # Mode selection
    if mode == 'Kerr Rotation':
        values = 'Kerr Rotation (deg)'
    elif mode == 'Reflectivity':
        values = 'Reflectivity (V)'
    elif mode == 'Derivative Coercivity':
        values = 'Derivative Coercivity (T)'
    elif mode == 'Measured Coercivity':
        values = 'Measured Coercivity (T)'
    else:
        values = 'Kerr Rotation (deg)'

    # Create a dataframe formatted as the 2d map
    heatmap_data = database.pivot_table(
        index='y_pos (mm)',
        columns='x_pos (mm)',
        values=values,
    )

    # Min and max values for colorbar fixing
    z_min = database[values].min()
    z_max = database[values].max()
    z_mid = (z_min + z_max) / 2


    # Generate the heatmap plot from the dataframe
    heatmap = go.Heatmap(
        x=heatmap_data.columns,
        y=heatmap_data.index,
        z=heatmap_data.values,
        colorscale='Rainbow',
        # Set ticks for the colorbar
        colorbar=dict(
            title='',  # Title for the colorbar
            tickvals=[z_min, (z_min + z_mid) / 2, z_mid, (z_max + z_mid) / 2, z_max],  # Tick values
            ticktext=[f'{z_min:.2f}', f'{(z_min + z_mid) / 2:.2f}', f'{z_mid:.2f}', f'{(z_max + z_mid) / 2:.2f}',
                      f'{z_max:.2f}']  # Tick text
        )
    )

    title = 'Map of MOKE points <br>' + title

    # Make and show figure
    fig = go.Figure(data=[heatmap], layout=layout)

    return fig


def data_plot(folderpath, target_x, target_y, measurement_id):
    data = load_measurement_files(folderpath, target_x, target_y, measurement_id)

    fig = go.Figure()

    # First plot
    fig.update_xaxes(title_text='Time (s)')
    fig.update_yaxes(title_text='Voltage (V)')

    fig.add_trace(go.Scatter(x=data.index, y=data['Magnetization'],
                             mode='lines', line=dict(color='SlateBlue', width=3))
                  )
    fig.add_trace(go.Scatter(x=data.index, y=data['Pulse'],
                             mode='lines', line=dict(color='Green', width=3))
                  )
    fig.add_trace(go.Scatter(x=data.index, y=data['Sum'],
                             mode='lines', line=dict(color='Crimson', width=3))
                  )

    fig.update_layout(
        # legend=dict(
        #     x=0.1,  # X position (0-1)
        #     y=0.1,  # Y position (0-1)
        #     xanchor="center",  # Anchor point for x
        #     yanchor="top"  # Anchor point for y
        # ),
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig

def loop_plot(folderpath, target_x, target_y, measurement_id):
    pulse_voltage = get_pulse_voltage(folderpath) / 100
    data = load_measurement_files(folderpath, target_x, target_y, measurement_id)
    data = calculate_loop_from_data(data, pulse_voltage, coil_factor=0.92667)

    fig = go.Figure()

    # First plot
    fig.update_xaxes(title_text='Field (T)')
    fig.update_yaxes(title_text='Kerr roation (deg)')

    fig.add_trace(go.Scatter(x=data['Field'], y=data['Magnetization'],
                             mode='markers', line=dict(color='SlateBlue', width=3))
                  )

    fig.update_layout(
        # legend=dict(
        #     x=0.1,  # X position (0-1)
        #     y=0.1,  # Y position (0-1)
        #     xanchor="center",  # Anchor point for x
        #     yanchor="top"  # Anchor point for y
        # ),
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig


def loop_derivative_plot(folderpath, target_x, target_y, measurement_id):
    pulse_voltage = get_pulse_voltage(folderpath) / 100
    data = load_measurement_files(folderpath, target_x, target_y, measurement_id)
    data = calculate_loop_from_data(data, pulse_voltage, coil_factor=0.92667)
    data['Derivative'] = data['Magnetization'] - data['Magnetization'].shift(1)
    data.loc[np.abs(data['Field']) < 1e-3, 'Derivative'] = 0 # Avoid derivative discrepancies around 0 Field

    fig = go.Figure()

    # First plot
    fig.update_xaxes(title_text='Field (T)')
    fig.update_yaxes(title_text='Kerr roation (deg)')

    fig.add_trace(go.Scatter(x=data['Field'], y=data['Magnetization'],
                             mode='markers', line=dict(color='SlateBlue', width=3))
                  )

    fig.add_trace(go.Scatter(x=data['Field'], y=data['Derivative'], mode='markers',
                             line=dict(color='Firebrick', width=3)))

    fig.update_layout(
        # legend=dict(
        #     x=0.1,  # X position (0-1)
        #     y=0.1,  # Y position (0-1)
        #     xanchor="center",  # Anchor point for x
        #     yanchor="top"  # Anchor point for y
        # ),
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig

