"""
Functions used in MOKE interactive plot using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: Pierre Le Berre - Institut Néel (pierre.le-berre@neel.cnrs.fr)
"""

import pandas as pd
import xarray as xr
from pathlib import Path
from plotly.subplots import make_subplots
from scipy.signal import savgol_filter
from collections import defaultdict
import re

from ..functions.functions_shared import *

def read_info_file(folderpath: Path):
    """
    Read info.txt and extract necessary parameters for further treatment

    Parameters:
        folderpath(pathlib.Path) : path to the folder containing info.txt (usually the same as the measurements)

    Returns:
        dictionary
    """

    infopath = folderpath / 'info.txt'
    try:
        with open(infopath, "r", encoding="iso-8859-1") as file_info:
            for line in file_info:
                if "Pulse_voltage" in line:
                    pulse_volt = int(line.split("=")[1])
                if "Average_per_point" in line:
                    avg_pts = int(line.split("=")[1])
                if 'Number_of_points_x' in line:
                    x_points = int(line.split("=")[1])
                if "Number_of_points_y" in line:
                    y_points = int(line.split("=")[1])

        info = { 'pulse_voltage' : pulse_volt,
                 'shots_per_point' : avg_pts,
                 'x_dimension' : x_points,
                 'y_dimension' : y_points,

        }
        return info
    except FileNotFoundError:
        return None



def load_target_measurement_files(folderpath: Path, target_x: float, target_y: float, measurement_nb: int = 0):
    """
        For a given x and y position and measurement number, find and load corresponding measurement

        Parameters:
            folderpath(pathlib.Path) : path to the folder containing info.txt (usually the same as the measurements)
            target_x(float) : x position of targeted measurement
            target_y(float) : y position of targeted measurement
            measurement_nb(int) : for multiple acquisition per points, specify which one should be loaded. If 0, measurements will be averaged (default)

        Returns:
            pd.Dataframe
    """
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

    # measurement_id = 0 returns average over all measurements
    if measurement_nb == 0:
        data = pd.DataFrame({'Magnetization': mag.mean(axis=1),
                             'Pulse': pulse.mean(axis=1),
                             'Sum': sum.mean(axis=1)
                             })

    elif measurement_nb > 0:
        idx = measurement_nb-1
        data = pd.DataFrame({'Magnetization': mag.iloc[:, idx],
                             'Pulse': pulse.iloc[:, idx],
                             'Sum': sum.iloc[:, idx]
                             })

    else:
        raise ValueError('Measurement number invalid, either out of range or not an integer')

    return data


def treat_data(data: pd.DataFrame, folderpath:Path, coil_factor:float=0.92667, correct_offset:bool=True,
               smooth:bool=True, smooth_window_length:int=61, smooth_polyorder:int=1, filter_zero:bool=True):
    """
        Calculate the field by integrating over the pulse signal and then normalizing by the instrumental parameters

        Parameters:
            data(pd.Dataframe) : data for which the field needs to be calculated
            pulse_voltage(float) : Recorded pulse voltage from the measurement, can be found in info.txt file
            coil_factor(float) : Calibration factor for the coil. Current default = 0.92667 T / 100 V (05/11/2024)
        Returns:
            pd.Dataframe
    """

    pulse_voltage = read_info_file(folderpath)['pulse_voltage']
    max_field = coil_factor/100 * pulse_voltage

    pos_start = 330
    pos_end = 670
    neg_start = 1330
    neg_end = 1670

    # Remove pulse noise to isolate actual pulse signal
    data['Pulse'] = data['Pulse'].replace(0.0016667, 0)
    data['Pulse'] = data['Pulse'].replace(-0.0016667, 0)

    # Integrate pulse during triggers to get field
    data.loc[pos_start:pos_end, 'Field'] = data.loc[pos_start:pos_end, 'Pulse'].cumsum()
    data.loc[neg_start:neg_end, 'Field'] = data.loc[neg_start:neg_end, 'Pulse'].cumsum()

    # Set field using coil parameters
    midpoint = len(data) // 2
    data.loc[:midpoint, 'Field'] = data.loc[:midpoint, 'Field'].apply(
        lambda x: -x * max_field / np.abs(data['Field'].min()))
    data.loc[midpoint:, 'Field'] = data.loc[midpoint:, 'Field'].apply(
        lambda x: -x * max_field / np.abs(data['Field'].max()))

    # Correct offset
    if correct_offset:
        offset = data['Magnetization'].mean()
        data['Magnetization'] = data['Magnetization'].apply(lambda x: x - offset)

    # Data smoothing
    if smooth:
        data['Magnetization'] = savgol_filter(data['Magnetization'], smooth_window_length, smooth_polyorder)

    # Remove oddities around H=0 by forcing points in the positive(negative) loop to be over(under) a threshold
    if filter_zero:
        data.loc[pos_start:pos_end, 'Field'] = data.loc[pos_start:pos_end, 'Field'].where(data['Field'] > 2e-3)
        data.loc[neg_start:neg_end, 'Field'] = data.loc[neg_start:neg_end, 'Field'].where(data['Field'] < -2e-3)

    return data



def extract_loop_section(data: pd.DataFrame):
    """
          From a dataframe, select only the parts where the field is defined, resulting in a section containing only the loop

          Parameters:
              data(pd.Dataframe) : source dataframe with a 'Field' column
          Returns:
              pd.Dataframe
    """
    # Keep only the points where field is defined, removing points outside of pulse
    try:
        non_nan = data[data['Field'].notna()].index.values
        loop_section = data.loc[non_nan, :]
        loop_section.reset_index(drop=True, inplace=True)
        return loop_section
    except NameError:
        raise NameError('Field column not defined')



def calc_max_kerr_rotation(data:pd.DataFrame):
    """
        From a dataframe, return the value for the saturation Kerr rotation

        Parameters:
            data(pd.Dataframe) : source dataframe with a 'Magnetization' column

        Returns:
            float
    """
    try:
        kerr_max = data['Magnetization'].max()
        kerr_min = data['Magnetization'].min()
        kerr_mean = (kerr_max + np.abs(kerr_min))/2
        return kerr_mean
    except NameError:
        raise NameError('Magnetization column not defined')


def calc_reflectivity(data:pd.DataFrame):
    """
          From a dataframe, return the value for the reflectivity Kerr rotation

          Parameters:
              data(pd.Dataframe) : source dataframe with a 'Sum' column

          Returns:
              float
    """
    try:
        reflectivity = data['Sum'].mean(axis=0)
        return reflectivity
    except NameError:
        raise NameError('Sum column not defined')


def calc_derivative_coercivity(data:pd.DataFrame):
    """
            From a dataframe, return the field values for the extremes of dM/dH

            Parameters:
               data(pd.Dataframe) : source dataframe with a 'Field' and 'Magnetization' column

            Returns:
               float, float
    """
    data['Derivative'] = data['Magnetization'] - data['Magnetization'].shift(1)
    data.loc[np.abs(data['Field']) < 2e-3, 'Derivative'] = 0 # Avoid derivative discrepancies around 0 Field

    # For positive / negative field, find index of maximum / minimum derivative and extract corresponding field
    coercivity_positive = data.loc[data.loc[data['Field'] > 0, 'Derivative'].idxmax(), 'Field']
    coercivity_negative = data.loc[data.loc[data['Field'] < 0, 'Derivative'].idxmin(), 'Field']

    return coercivity_positive, coercivity_negative


def calc_mzero_coercivity(data:pd.DataFrame):
    """
           From a dataframe, return the field values where Magnetization is closest to 0

           Parameters:
               data(pd.Dataframe) : source dataframe with a 'Field' and 'Magnetization' column

           Returns:
               float, float
    """
    coercivity_positive = data.loc[np.abs(data.loc[data['Field'] > 0, 'Magnetization']).idxmin(), 'Field']
    coercivity_negative = data.loc[np.abs(data.loc[data['Field'] < 0, 'Magnetization']).idxmin(), 'Field']

    return coercivity_positive, coercivity_negative


def make_database(folderpath:Path, coil_factor:float=0.92667):
    pulse_voltage = read_info_file(folderpath)['pulse_voltage']

    # Regular expression to match 'p' followed by a number
    pattern = re.compile(r'p(\d+)')

    grouped_files = defaultdict(list)

    # Use glob to iterate through the files and group them by p-number
    for filepath in folderpath.glob('p*.txt'):
        match = pattern.search(filepath.name)
        if match:
            number = match.group(1)  # Extract the p-number
            grouped_files[number].append(filepath)

    # Initialize Dataframe
    database = pd.DataFrame()

    # Iterate over measurement files
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

        data = treat_data(data, folderpath, coil_factor=0.92667, correct_offset=True, smooth=True, smooth_window_length=61, smooth_polyorder=1, filter_zero=True)

        # Get max Kerr rotation
        kerr_mean = calc_max_kerr_rotation(data)

        # Get reflectivity
        reflectivity = calc_reflectivity(data)

        # Get coercivity from maximum derivative
        d_coercivity = np.mean(calc_derivative_coercivity(data))

        # Get M=0 coercivity
        m_coercivity = np.mean(calc_mzero_coercivity(data))

        # Assign to database
        database.loc[i, 'File Number'] = number
        database.loc[i, 'Ignore'] = 0
        database.loc[i, 'x_pos (mm)'] = float(path.name.split('_')[1].lstrip('x'))
        database.loc[i, 'y_pos (mm)'] = float(path.name.split('_')[2].lstrip('y'))
        database.loc[i, 'Kerr Rotation (deg)'] = kerr_mean
        database.loc[i, 'Reflectivity (V)'] = reflectivity
        database.loc[i, 'Derivative Coercivity (T)'] = d_coercivity
        database.loc[i, 'Measured Coercivity (T)'] = m_coercivity

    database_path = folderpath / (folderpath.name + '_database.csv')

    date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    app_version = get_version('app')
    database_version = get_version('moke')

    metadata = [f"Date of fitting: {date}",
                f"Code version: {app_version}",
                'Database type: Moke',
                f'Moke database version = {database_version}',
                f'Coil factor = {coil_factor}']

    save_with_metadata(database, database_path, metadata=metadata)
    return database_path


def heatmap_plot(database_path, mode, title='', z_min=None, z_max=None, masking=False):
    database = pd.read_csv(database_path, comment = '#')

    # Exit if no database is found
    if database is None:
        return go.Figure(layout=heatmap_layout())

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

    # If mask is set, hide points that have an ignore tag in the database
    if masking:
        # Create a mask to hide ignored points
        mask_data = database.pivot_table(
            index = 'y_pos (mm)',
            columns='x_pos (mm)',
            values='Ignore'
        )
        # Ignore points
        mask = (mask_data == 0)

        heatmap_data = heatmap_data.where(mask, np.nan)


    # Min and max values for colorbar fixing
    if z_min is None:
        z_min = np.nanmin(heatmap_data.values)
    if z_max is None:
        z_max = np.nanmax(heatmap_data.values)

    # Get unit from selected mode for colorbar title
    unit = values.split(' ')[-1]

    # Generate the heatmap plot from the dataframe
    heatmap = go.Heatmap(
        x=heatmap_data.columns,
        y=heatmap_data.index,
        z=heatmap_data.values,
        colorscale='Rainbow',
        # Set ticks for the colorbar
        colorbar=colorbar_layout(z_min, z_max, title=unit)
    )

    title = f'{mode} MOKE map <br>' + title

    # Make and show figure
    fig = go.Figure(data=[heatmap], layout=heatmap_layout(title))

    if z_min is not None:
        fig.data[0].update(zmin=z_min)
    if z_max is not None:
        fig.data[0].update(zmax=z_max)

    return fig

def blank_plot():
    fig = go.Figure()

    fig.update_xaxes(title_text='Time (s)')
    fig.update_yaxes(title_text='Voltage (V)')

    fig.update_layout(
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig


def data_plot(data):
    fig = go.Figure()

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
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig

def loop_plot(data):
    data = extract_loop_section(data)

    fig = go.Figure()

    # First plot
    fig.update_xaxes(title_text='Field (T)')
    fig.update_yaxes(title_text='Kerr roation (deg)')

    fig.add_trace(go.Scatter(x=data['Field'], y=data['Magnetization'],
                             mode='markers', line=dict(color='SlateBlue', width=3))
                  )

    fig.update_layout(
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig


def loop_derivative_plot(data):
    data = extract_loop_section(data)
    data['Derivative'] = data['Magnetization'] - data['Magnetization'].shift(1)
    data.loc[np.abs(data['Field']) < 1e-3, 'Derivative'] = 0 # Avoid derivative discrepancies around 0 Field

    fig = go.Figure()

    # First plot
    fig.update_xaxes(title_text='Field (T)')
    fig.update_yaxes(title_text='Kerr roation (deg)')

    fig.add_trace(go.Scatter(x=data['Field'], y=data['Magnetization'],
                             mode='markers', line=dict(color='SlateBlue', width=3))
                  )

    fig.add_trace(go.Scatter(x=data['Field'], y=data['Derivative'].apply(lambda x: 10*x), mode='markers',
                             line=dict(color='Firebrick', width=3)))

    fig.update_layout(
        height=700,
        width=1100,
        title_text='',
        showlegend=False
    )

    return fig


def loop_map_plot(folderpath, database_path):
    database = pd.read_csv(database_path, comment='#')

    x_min, x_max = database['x_pos (mm)'].min(), database['x_pos (mm)'].max()
    y_min, y_max = database['y_pos (mm)'].min(), database['y_pos (mm)'].max()

    info_file = read_info_file(folderpath)
    x_dim, y_dim = info_file['number_of_points_x'], info_file['number_of_points_y']

    step_x = (np.abs(x_max) + np.abs(x_min)) / (x_dim-1)
    step_y = (np.abs(y_max) + np.abs(y_min)) / (y_dim-1)

    fig = make_subplots(rows=y_dim, cols=x_dim, horizontal_spacing=0.001, vertical_spacing=0.001)

    # Update layout to hide axis lines, grid, and ticks for each subplot
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)

    # Update layout for aesthetics
    fig.update_layout(height=1200, width=1200, title_text="Blobs", showlegend=False,
                      plot_bgcolor='white')

    pulse_voltage = info_file['pulse_voltage'] / 100

    for pair in list(zip(database['x_pos (mm)'], database['y_pos (mm)'])):
        target_x = pair[0]
        target_y = pair[1]


        data = load_target_measurement_files(folderpath, target_x, target_y, measurement_id=0)
        data = treat_data(data, folderpath)
        data = extract_loop_section(data)

        col = int((target_x/step_x + (x_dim+1)/2))
        row = int((-target_y/step_y + (y_dim+1)/2))

        fig.add_trace(go.Scatter(x=data['Field'], y=data['Magnetization'],
                                 mode='lines', line=dict(color='SlateBlue', width=1)
                      ), row=row, col=col)


    return fig