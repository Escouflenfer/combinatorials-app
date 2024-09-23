import numpy as np
import pandas as pd
import re
from scipy.optimize import least_squares
from scipy.signal import savgol_filter
from scipy.stats import linregress
from natsort import natsorted
from IPython.display import clear_output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from pathlib import Path


def pairwise(list):
    a = iter(list)
    return zip(a, a)


def get_database_path(folderpath):
    database_path = None
    for path in folderpath.glob('*.csv'):
        if database_path is None:
            database_path = path
        elif database_path is not None:
            raise NameError('Multiple .csv files found, check your folder')
    if database_path is None:
        return None
    return folderpath / database_path


def get_row_number(database, target_x, target_y):
    test = (database['x_pos (mm)'] == target_x) & (database['y_pos (mm)'] == target_y)
    row_number = (database[test].index[0])
    return row_number


def get_asc2d_path(folderpath, target_x, target_y):
    asc2d_filepath = None
    # Attempt to locate database, returns None if database is not found
    database_path = get_database_path(folderpath)

    # If database exists, load it
    if database_path is not None:
        database = pd.read_csv(database_path)
        # If database contains a File_id column, get the index and extract the filename (fast and reliable)
        if 'File_id' in database.columns:
            row_number = get_row_number(database, target_x, target_y)
            filename = database['File_id'].loc[row_number]
            asc2d_filepath = folderpath / filename
        # If database does not contain a File_id column, get the file number and the index (fast but not reliable)
        else:
            file_number = get_row_number(database, target_x, target_y) + 1
            for filename in folderpath.glob(f'*_{file_number}.asc2d'):
                asc2d_filepath = folderpath / filename
    # If database does not exist, scan all files for position (slow and reliable)
    elif database_path is None:
        filename = scan_for_position(folderpath, target_x, target_y)
        asc2d_filepath = folderpath / filename

    # Double check that the proper file is loaded
    x, y = get_position(asc2d_filepath)
    if x == target_x and y == target_y:
        return asc2d_filepath
    else:
        error_msg = 'Position logged in file differs from position in database. File loaded was ' + str(asc2d_filepath)
        raise ValueError(error_msg)


def get_position(filepath):
    with open(filepath, 'r') as file:
        header = [next(file) for _ in range(46)]
    target_name = header[8]
    pattern = r'\((\d+),(\d+)\)'
    match = re.search(pattern, target_name)
    x = (int(match.group(2)) - 10) * 5  # Header tuple has the format (y,x)
    y = (10 - int(match.group(1))) * 5
    return x, y

def scan_for_position(folderpath, target_x, target_y):
    for path in folderpath.glob('*.asc2d'):
        position = get_position(path)
        if position[0] == target_x and position[1] == target_y:
            return path


def format_dataframe(df):
    # Rename columns and reset index to fit the format:
    # df = df.reset_index().drop('index', axis = 1)
    df.rename(columns={' z(raw/unitless)': 'Total Profile (nm)'}, inplace=True)
    df.rename(columns={'y(um)': 'Distance (um)'}, inplace=True)
    return df


def level_data(df, step=100):
    # Calculate and remove linear component from profile with step point linear fit
    slope = (np.mean(df.iloc[-step:-1, 1].tolist()) - np.mean(df.iloc[0:step, 1].tolist())) / df.iat[-1, 0]
    df['Fitted Profile (nm)'] = df['Total Profile (nm)'] - df['Distance (um)'] * slope - df.iat[0, 1]
    return slope, df


def treat_data(df):
    # Treat the dataframe with all steps of the process at once, making it ready for measurement
    df = format_dataframe(df)
    slope, df = level_data(df)
    return slope, df


def derivate_data(df):
    # Ensure the DataFrame has the column 'Total Profile (nm)'
    if 'Total Profile (nm)' not in df.columns:
        raise ValueError("The DataFrame must contain a 'Total Profile (nm)' column. "
                         "Make sure to run Format_dataframe function first.")
    # Calculate point to point derivative
    df['Derivative'] = df['Total Profile (nm)'].diff().fillna(0)
    return df


def find_first_step(df, bound = 350, step = 0.25):
    df = derivate_data(df)
    df_head = df.head(int(bound/step))
    max_index = df_head['Derivative'].idxmax()
    step_position = df_head.loc[max_index, 'Distance (um)']
    return step_position


def multi_step_function(x, *params):
    # Generate function with multiple steps
    # Even indices are the x positions of the steps,
    # Odd indices are the y values after each step.

    y = np.full_like(x, params[1])
    for i in range(0, len(params) - 2, 2):
        x0 = params[i]
        y1 = params[i + 3]
        y = np.where(x >= x0, y1, y)
    return y


def generate_parameters(height, x0, length = 101, n_steps = 20):
    guess = []
    for n in range(n_steps+1):
        guess.append(x0+2*length*n) # Step up position
        guess.append(height) # Step up height
        guess.append(x0+length+2*length*n) # Step down position
        guess.append(0) # Step down height
    return guess


def generate_bounds(min_lower=-100, min_upper=20, n_steps=20):
    lower_bounds = [-np.inf]
    upper_bounds = [np.inf]
    for n in range(n_steps+1):
        lower_bounds.append(min_lower)
        upper_bounds.append(min_upper)
        lower_bounds.append(-np.inf)
        upper_bounds.append(np.inf)
    return (lower_bounds, upper_bounds)

def residuals(params, x, y):
    # Loss function for fitting
    return y - multi_step_function(x, *params)

def fit_data(data, guess):
    x_data = data['Distance (um)']
    y_data = data['Fitted Profile (nm)']
    result = least_squares(residuals, guess, args=(x_data, y_data), loss='soft_l1')
    fitted_params = result.x
    return fitted_params


def extract_fit(fitted_params):
    # Separate fitted parameters
    fit_position_list = []
    fit_height_list = []
    for position, height in pairwise(fitted_params):
        fit_position_list.append(np.round(position, 1))
        fit_height_list.append(np.round(height, 1))

    # From fitted parameters, calculate positions
    position_list = []
    for n in range(len(fit_position_list) - 1):
        a = fit_position_list[n]
        b = fit_position_list[n + 1]
        position_list.append(np.round(np.abs(b - (b - a) / 2), 1))
    position_list.pop()

    # From fitted paramters, calculate heights
    height_list = []
    for n in range(len(fit_height_list) - 1):
        a = fit_height_list[n]
        b = fit_height_list[n + 1]
        height_list.append(np.round(np.abs(a - b), 1))
    height_list.pop()

    return position_list, height_list


def blank_heatmap(radius=40, step=5, title=''):
    # Create a grid of x and y values
    x = np.arange(-radius, radius + step, step)
    y = np.arange(-radius, radius + step, step)

    # Initialize the z array with zeros
    z = np.full((len(y), len(x)), np.nan)

    # Create a circular mask: points within the radius are set to 1
    for i in range(len(y)):
        for j in range(len(x)):
            if np.sqrt(x[j] ** 2 + y[i] ** 2) <= radius:
                z[i, j] = 1

    # Create the heatmap
    heatmap = go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale='Rainbow'
    )

    # Set up the layout
    layout = go.Layout(
        title=title,
        xaxis=dict(title='X (mm)'),
        yaxis=dict(title='Y (mm)'),
        width=700,
        height=700
    )

    # Make and show figure
    fig = go.Figure(data=[heatmap], layout=layout)

    return fig

def heatmap_plot(database, mode = 'Thickness', title = ''):
    if database is None:
        return go.Figure()
    # Mode selection
    if mode == 'Thickness':
        values = 'Mean_step_height (nm)'
    elif mode == 'Standard Deviation':
        values = 'Std_step_height (nm)'
    elif mode == 'Gradient':
        values = 'Gradient_slope (nm/mm)'
    else:
        values = 'Mean_step_height (nm)'

    # Create a dataframe formatted as the 2d map
    heatmap_data = database.pivot_table(
        index='y_pos (mm)',
        columns='x_pos (mm)',
        values=values,
    )

    # Generate the heatmap plot from the dataframe
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
        colorbar=dict(
            title='(nm) <br>&nbsp;<br>',
            tickfont=dict(size=15),
            titlefont=dict(size=18),
            tickvals=[z_min, (z_min + z_mid) / 2, z_mid, (z_max + z_mid) / 2, z_max],  # Tick values
            ticktext=[f'{z_min:.2f}', f'{(z_min + z_mid) / 2:.2f}', f'{z_mid:.2f}', f'{(z_max + z_mid) / 2:.2f}',
                      f'{z_max:.2f}'],  # Tick text
        )

    )

    title = 'Thickness map <br>' + title
    # Plot parameters
    layout = go.Layout(
        title=title,
        titlefont=dict(size=20),
        xaxis=dict(title='X (mm)', tickfont=dict(size=15), titlefont=dict(size=18)),
        yaxis=dict(title='Y (mm)', tickfont=dict(size=15), titlefont=dict(size=18)),
        height=700,
        width=700
    )

    # Make and show figure
    fig = go.Figure(data=[heatmap], layout=layout)

    return fig


def profile_plot(folderpath, target_x, target_y):
    database_path = get_database_path(folderpath)
    if database_path is None:
        filepath = scan_for_position(folderpath, target_x, target_y)
    elif database_path is not None:
        database = pd.read_csv(get_database_path(folderpath))
        rownumber = get_row_number(database, target_x, target_y)
        database_slice = database.loc[rownumber, :]
        filepath = folderpath / Path(database_slice['File_id'])

        # Extract fitted parameters from database for plotting
        flatten_slope = database_slice.loc['Flatten_slope (nm/mm)']
        fitted_params = database_slice.iloc[8:].values
        position_list, height_list = extract_fit(fitted_params)
        gradient_slope = database_slice.loc['Gradient_slope (nm/mm)']
        gradient_intercept = database_slice.loc['Gradient_intercept (nm)']
    else:
        return go.Figure()

    asc2d_dataframe = pd.read_csv(filepath, skiprows=46)
    _, asc2d_dataframe = treat_data(asc2d_dataframe)

    # Plot the data
    fig = make_subplots(
        rows=3,
        cols=1,
        row_heights=[0.3, 0.4, 0.3],
        subplot_titles=("Raw data", "Fitted data", "Measured thicknesses"),
        shared_xaxes=True,
        vertical_spacing=0.1
    )

    # First plot
    fig.update_xaxes(title_text='Distance (um)', row=1, col=1)
    fig.update_yaxes(title_text='Profile (nm)', row=1, col=1)
    # Measured profile
    fig.add_trace(
        go.Scatter(x=asc2d_dataframe['Distance (um)'], y=asc2d_dataframe['Total Profile (nm)'],
                   mode='lines',
                   # name='Measured profile',
                   line=dict(color='SlateBlue ', width=3)),
        row=1, col=1
    )
    # Linear component
    try:
        fig.add_trace(
            go.Scatter(x=asc2d_dataframe['Distance (um)'],
                       y=(asc2d_dataframe['Distance (um)'] * flatten_slope) + asc2d_dataframe.iat[0, 1],
                       mode='lines',
                       name='Linear component',
                       line=dict(color='Crimson', width=2)),
            row=1, col=1
        )
    except NameError:
        pass

    # Second plot
    fig.update_xaxes(title_text='Distance (um)', row=2, col=1)
    fig.update_yaxes(title_text='Profile (nm)', row=2, col=1)
    # Flattened profile
    fig.add_trace(
        go.Scatter(x=asc2d_dataframe['Distance (um)'], y=asc2d_dataframe['Fitted Profile (nm)'],
                   mode='lines',
                   # name='Flattened profile',
                   line=dict(color='SlateBlue ', width=3)),
        row=2, col=1
    )
    # Fitted step function
    try:
        fig.add_trace(
            go.Scatter(x=asc2d_dataframe['Distance (um)'],
                       y=multi_step_function(asc2d_dataframe['Distance (um)'], *fitted_params),
                       mode='lines',
                       # name='Fitted step function',
                       line=dict(color='Crimson', width=2)),
            row=2, col=1
        )
    except NameError:
        pass

    # Third plot
    fig.update_xaxes(title_text='Distance (um)', row=3, col=1)
    fig.update_yaxes(title_text='Thickness (nm)', row=3, col=1)
    try:
        # Scattered heights
        fig.add_trace(
            go.Scatter(x=position_list, y=height_list,
                       mode='markers',
                       # name='Measured thickness',
                       line=dict(color='SlateBlue ', width=3)),
            row=3, col=1
        )
        # Mean line
        fig.add_hline(y=database_slice.loc['Mean_step_height (nm)'], row=3, col=1)

        # Linear gradient fit
        fig.add_trace(
            go.Scatter(x=asc2d_dataframe['Distance (um)'],
                       y=(gradient_intercept + (gradient_slope/1000) * asc2d_dataframe['Distance (um)']),
                       mode='lines',
                       # name=('Linear gradient fit. a = ' + str(gradient_slope) + 'nm/mm'),
                       line=dict(color='Crimson', width=2)),
            row=3, col=1
        )
    except NameError:
        pass

    fig.update_layout(
        # legend=dict(
        #     x=0.1,  # X position (0-1)
        #     y=0.1,  # Y position (0-1)
        #     xanchor="center",  # Anchor point for x
        #     yanchor="top"  # Anchor point for y
        # ),
        height=700,
        width=1100,
        title_text=f"{filepath.name}, x = {get_position(filepath)[0]} y = {get_position(filepath)[1]}",
        showlegend=False
    )

    return fig


def fit_plot(fig, df_raw, *fitted_params):
    position_list, height_list = extract_fit(fitted_params)
    linear_fit = linregress(position_list, height_list)
    gradient_slope = linear_fit.slope
    gradient_intercept = linear_fit.intercept

    # Second plot
    fig.update_xaxes(title_text='Distance (um)', row=2, col=1)
    fig.update_yaxes(title_text='Profile (nm)', row=2, col=1)

    # Fitted step function
    fig.add_trace(
        go.Scatter(x=df_raw['Distance (um)'], y=multi_step_function(df_raw['Distance (um)'], *fitted_params),
                   mode='lines',
                   name='Fitted step function',
                   line=dict(color='LimeGreen', width=2)),
        row=2, col=1
    )

    # Third plot
    fig.update_xaxes(title_text='Distance (um)', row=3, col=1)
    fig.update_yaxes(title_text='Thickness (nm)', row=3, col=1)
    # Scattered heights
    fig.add_trace(
        go.Scatter(x=position_list, y=height_list,
                   mode='markers',
                   name='Measured thickness',
                   line=dict(color='LimeGreen', width=2)),
        row=3, col=1
    )
    # Mean line
    fig.add_hline(y=np.mean(height_list), row=3, col=1)

    # Linear gradient fit
    fig.add_trace(
        go.Scatter(x=df_raw['Distance (um)'], y=(gradient_intercept + gradient_slope * df_raw['Distance (um)']),
                   mode='lines',
                   name=('Linear gradient fit, a = ' + str(gradient_slope) + 'nm/mm'),
                   line=dict(color='LimeGreen', width=2)),
        row=3, col=1
    )

    return fig


def batch_fit(folderpath):
    folderpath = Path(folderpath)
    files = []
    for path in folderpath.glob('*.asc2d'):
        files.append(path)

    # Prepare a dataframe for export
    export = pd.DataFrame()

    i = -1
    for n in natsorted(files):
        i += 1
        clear_output()
        print(n)
        filepath = folderpath / n

        # Read header to extract measured point position
        x, y = get_position(filepath)

        # Read and treat data
        data = pd.read_csv(filepath, skiprows=46)
        slope, data = treat_data(data)

        x0 = find_first_step(data)

        x_data = data['Distance (um)']
        y_data = data['Fitted Profile (nm)']

        y_data = savgol_filter(y_data, 41, 5)

        guess = generate_parameters(height=150, x0=x0)

        # Fit the multi-step function to the data
        result = least_squares(residuals, guess, jac='2-point', args=(x_data, y_data), loss='soft_l1')
        fitted_params = result.x

        position_list, height_list = extract_fit(fitted_params)

        linear_fit = linregress(position_list, height_list)

        export.loc[i, 'File_id'] = filepath.name
        export.loc[i, 'x_pos (mm)'] = x
        export.loc[i, 'y_pos (mm)'] = y
        export.loc[i, 'Mean_step_height (nm)'] = np.mean(height_list).round(1)
        export.loc[i, 'Std_step_height (nm)'] = np.std(height_list).round(1)
        export.loc[i, 'Flatten_slope (nm/mm)'] = slope.round(3)
        export.loc[i, 'Gradient_slope (nm/mm)'] = (1000 * linear_fit.slope).round(3)
        export.loc[i, 'Gradient_intercept (nm)'] = linear_fit.intercept.round(3)
        for n in range(len(fitted_params)):
            height_column = f'Fit_parameter_{n}'
            export.loc[i, height_column] = fitted_params[n]

    database_path = folderpath / (folderpath.parent.name +'_database.csv')
    print(database_path)
    export.to_csv(database_path, index=False)
    print('Done. Database saved at ', database_path)


def replace_fit(folderpath, target_x, target_y, fitted_params):
    database = pd.read_csv(get_database_path(folderpath))
    rownumber = get_row_number(database, target_x, target_y)

    position_list, height_list = extract_fit(fitted_params)
    linear_fit = linregress(position_list, height_list)

    if database.loc[rownumber, 'x_pos (mm)'] == target_x and database.loc[rownumber, 'y_pos (mm)'] == target_y:
        database.loc[rownumber, 'Mean_step_height (nm)'] = np.mean(height_list).round(1)
        database.loc[rownumber, 'Std_step_height (nm)'] = np.std(height_list).round(1)
        database.loc[rownumber, 'Gradient_slope (nm/mm)'] = (1000 * linear_fit.slope).round(3)
        database.loc[rownumber, 'Gradient_intercept (nm)'] = linear_fit.intercept.round(3)
        for n in range(len(fitted_params)):
            height_column = f'Fit_parameter_{n}'
            database.loc[rownumber, height_column] = fitted_params[n]
        database.to_csv(get_database_path(folderpath), index=False)