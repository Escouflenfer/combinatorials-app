"""
Functions used in MOKE interactive plot using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import numpy as np
import plotly.graph_objects as go
import pandas as pd
from scipy.signal import savgol_filter


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

def get_measurement_number(folderpath):
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
    file = sorted(files)
    pulse = pd.read_table(files[0]).dropna(axis=1, how='all')
    mag = pd.read_table(files[1]).dropna(axis=1, how='all')
    sum = pd.read_table(files[2]).dropna(axis=1, how='all')


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
    data.loc[340:660, 'Field'] = data.loc[340:660, 'Pulse'].cumsum()
    data.loc[1340:1660, 'Field'] = data.loc[1340:1660, 'Pulse'].cumsum()
    # Correct field with coil parameters
    midpoint = len(data) // 2
    data.loc[:midpoint, 'Field'] = data.loc[:midpoint, 'Field'].apply(
        lambda x: -x * max_field / np.abs(data['Field'].min()))
    data.loc[midpoint:, 'Field'] = data.loc[midpoint:, 'Field'].apply(
        lambda x: -x * max_field / np.abs(data['Field'].max()))
    data['Magnetization'] = savgol_filter(data['Magnetization'], 41, 3)

    non_nan = data[data['Field'].notna()].index.values
    section = data.loc[non_nan, ('Magnetization', 'Field')]
    section.reset_index(drop=True, inplace=True)
    return section



def calculate_reflectivity(folderpath, target_x, target_y):
    for path in folderpath.glob('*_sum.txt'):
        file_x = float(path.name.split('_')[1].lstrip('x'))
        file_y = float(path.name.split('_')[2].lstrip('y'))
        if file_x == target_x and file_y == target_y:
            sum = pd.read_table(path)
            reflectivity = sum.mean()
            return reflectivity


def heatmap_plot(folderpath, selected_plot, title=''):
    df = pd.DataFrame()
    for idx, path in enumerate(folderpath.glob('*_magnetization.txt')):
        file_x = float(path.name.split('_')[1].lstrip('x'))
        file_y = float(path.name.split('_')[2].lstrip('y'))
        df.loc[idx, 'x (mm)'] = file_x
        df.loc[idx, 'y (mm)'] = file_y
        if selected_plot == 'Blank':
            df.loc[idx, 'z'] = np.sqrt(file_x**2 + file_y**2)
        elif selected_plot == 'Coercivity':
            df.loc[idx, 'z'] = np.sqrt(file_x**2 + file_y**2)
        elif selected_plot == 'Reflectivity':
            df.loc[idx, 'z'] = calculate_reflectivity(folderpath, file_x, file_y)


    # Create a dataframe formatted as the 2d map
    heatmap_data = df.pivot_table(
        index='y (mm)',
        columns='x (mm)',
        values='z',
    )

    z_min = 1
    z_max = 1
    z_mid = 1

    # Generate the heatmap plot from the dataframe
    heatmap = go.Heatmap(
        x=heatmap_data.columns,
        y=heatmap_data.index,
        z=heatmap_data.values,
        colorscale='Rainbow',
        colorbar=dict(
            title='',  # Title for the colorbar
            tickvals=[z_min, (z_min + z_mid) / 2, z_mid, (z_max + z_mid) / 2, z_max],  # Tick values
            ticktext=[f'{z_min:.2f}', f'{(z_min + z_mid) / 2:.2f}', f'{z_mid:.2f}', f'{(z_max + z_mid) / 2:.2f}',
                      f'{z_max:.2f}']  # Tick text
        )
    )

    title = 'Map of MOKE points <br>' + title
    # Plot parameters
    layout = go.Layout(
        title=title,
        xaxis=dict(range=[-50, 50], title='X (mm)'),
        yaxis=dict(range=[-50, 50], title='Y (mm)'),
        height=700,
        width=700
    )

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


def export_heatmap(fig, folderpath):
    name = folderpath.parent.name()

    fig.write_image(f"{name}.pdf", format="pdf")

