import os.path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import h5py
import shutil
from dash.exceptions import PreventUpdate
import functools
from plotly.subplots import make_subplots
from dash import Input, Output, State, ctx
from datetime import datetime
import re
import stringcase


# Decorator function to check conditions before executing callbacks, preventing errors
def check_conditions(conditions_function, hdf5_path_index):
    def decorator(callback_function):
        @functools.wraps(callback_function)
        def wrapper(*args, **kwargs):
            args = list(args)
            args[hdf5_path_index] = Path(args[hdf5_path_index])
            hdf5_path = args[hdf5_path_index]
            if not conditions_function(hdf5_path, *args, **kwargs):
                raise PreventUpdate
            return callback_function(*args, **kwargs)
        return wrapper
    return decorator


def cleanup_file(path):
    try:
        os.remove(path)
    except OSError:
        pass

def cleanup_directory(folderpath):
    for folder in os.listdir(folderpath):
        full_path = os.path.join(folderpath, folder)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)

def get_version(tag:str):
    """
    Scan the versions.txt file to extract version information.

    Parameters:
        tag (str): 'app', 'dektak', 'moke' Select which version to extract

    Returns:
        version (str): version of selected item
    """

    version_file_path = Path(os.path.abspath("./config/versions.txt"))
    with open(version_file_path, "r") as version_file:
        for line in version_file:
            if line.startswith(tag.strip()):
                version = line.split(" = ")[1]
                return version


def safe_glob(directory, pattern='*'):
    return [
        f for f in directory.glob(pattern)
        if f.is_file() and not (f.name.startswith('.') or f.name.startswith('._'))
    ]


def safe_rglob(directory, pattern='*'):
    return [
        f for f in directory.rglob(pattern)
        if f.is_file() and not f.name.startswith('.') and not f.name.startswith('._')
    ]


def is_macos_system_file(file_path):
    if type(file_path) is str:
        print(file_path)
        if '/._' not in file_path and not file_path.startswith('._'):
            return False
        else:
            return True
    if type(file_path) is Path:
        print(file_path.name)
        if not file_path.name.startswith('._'):
            return False
        else:
            return True


def unpack_zip_directory(filename_list: list, depth: int, remove_directories = True):
    for filename in filename_list:
        if filename.count('/') != depth:
            filename_list.remove(filename)
        elif remove_directories and filename.endswith('/'):
            filename_list.remove(filename)

    return filename_list


def detect_measurement(filename_list: list):
    """
       Scan a folder to determine which type of measurement it is

       Parameters:
           filename_list (list): list containing all filenames to parse

       Returns:
           version (str): detected measurement type
       """
    measurement_dict = {
        "Smartlab": ["ras"],
        "MOKE": ["log"],
        "EDX": ["spx"],
        "PROFIL": ["asc2d"],
        "ESRF": ["h5"],
        "XRD results": ["lst"]
    }

    for measurement_type, file_type in measurement_dict.items():
        for filename in filename_list:
            if filename.startswith('.'):  # Skip hidden files
                continue
            if filename.split('.')[-1] in file_type: # Check extensions for correspondence to the dictionary spec
                depth = filename.count('/')
                return measurement_type, depth
    return None


def get_sample_info_from_hdf5(hdf5_path):
    info_dict = {}

    with h5py.File(hdf5_path, "r") as f:
        sample_group = f['/sample']

        info_dict['sample_name'] = sample_group['sample_name'][()]
    return info_dict


def get_database_path(folderpath:Path):
    """
    Scan a folder to find a database file, tagged as *_database.csv

    Parameters:
        folderpath (pathlib.Path): Path to the folder containing the database

    Returns:
        database_path (pathlib.Path): Path to the database file within the specified folder
    """

    database_path = None
    for path in folderpath.glob("*_database.csv"):
        if database_path is None:
            database_path = path
        elif database_path is not None:
            raise NameError(
                "Multiple files ending in _database.csv found, check your folder"
            )
    if database_path is None:
        return None
    return folderpath / database_path


def compare_version(database_path: Path):
    metadata_dict = read_metadata(database_path)
    try:
        tag = metadata_dict["Database type"].lower()
        version = metadata_dict["Database version"]
        if version.strip() == get_version(tag).strip():
            return True
        else:
            return False

    except KeyError:
        return False


def save_with_metadata(df:pd.DataFrame, export_path:Path, metadata=None):
    """
    Save a dataframe to a csv while including metadata as comments (#).

    Parameters:
        df: The dataframe to be saved.
        export_path: The path to save the dataframe to.
        metadata: Metadata to be added to the dataframe.

    Returns:
        N/A. A file is created without returning anything
    """

    if metadata is None:
        metadata = {}

    with open(export_path, "w") as file:
        for key, line in metadata.items():
            file.write(f"# {key} = {line} \n")

    df.to_csv(export_path, mode="a", index=False)


def read_metadata(database_path):
    """
    For a given database path, read the metadata in the file, as marked by (#) tags

    Parameters:
        database_path (pathlib.Path): Path to the database file

    Returns:
        metadata (list): Metadata extracted from the database
    """

    metadata = {}
    with open(database_path, "r") as file:
        for line in file:
            if line.startswith("#"):
                line = line.strip('# ')
                try:
                    key, value = line.split(" = ")[0], line.split(" = ")[1].strip('\n')
                except IndexError:
                    key, value = line.split(": ")[0], line.split(": ")[1].strip('\n')
                metadata[key] = value

    return metadata


def heatmap_layout(title=""):
    """
    Generates a standardized layout for all heatmaps.

    Parameters:
        title (str): The title of the plot.

    Returns:
        go.Layout(): layout object that can be passed to a figure
    """
    layout = go.Layout(
        title=dict(text=title, font=dict(size=24)),
        xaxis=dict(title="X (mm)", tickfont=dict(size=24), title_font=dict(size=20), range=[-43, 43],
                   tickmode='linear', tick0=-40, dtick=10),
        yaxis=dict(title="Y (mm)", tickfont=dict(size=24), title_font=dict(size=20), range=[-43, 43],
                   tickmode='linear', tick0=-40, dtick=10),
        height=800,
        width=850,
        margin=dict(r=100, t=100)
    )
    return layout


def plot_layout(title=""):
    """
    Generates a standardized layout for all plots.

    Parameters:
        title (str): The title of the plot.

    Returns:
        go.Layout(): layout object that can be passed to a figure
    """
    layout = go.Layout(height=750, width=1100, title=title, showlegend=False)
    return layout


def colorbar_layout(z_min, z_max, precision=0, title=""):
    """
    Generates a standardized colorbar.

    Parameters:
        z_min : minimum value on the colorbar
        z_max : maximum value on the colorbar
        precision: number of digits on the colorbar scale
        title (str): The title of the plot.

    Returns:
        colorbar (dict): dictionary of colorbar parameters that can be passed to a figure
    """
    z_mid = (z_min + z_max) / 2
    colorbar = dict(
        title=dict(text=f"{title} <br>&nbsp;<br>", font=dict(size=20)),
        tickfont=dict(size=22),
        tickvals=[
            z_min,
            (z_min + z_mid) / 2,
            z_mid,
            (z_max + z_mid) / 2,
            z_max,
        ],  # Tick values
        ticktext=[
            f"{z_min:.{precision}f}",
            f"{(z_min + z_mid) / 2:.{precision}f}",
            f"{z_mid:.{precision}f}",
            f"{(z_max + z_mid) / 2:.{precision}f}",
            f"{z_max:.{precision}f}",
        ],  # Tick text
    )
    return colorbar


def significant_round(num, sig_figs):
    """
    Rounds a number to a specified number of significant figures.

    Parameters:
        num (float): The number to round.
        sig_figs (int): The number of significant figures to round to.

    Returns:
        float: The rounded number.
    """
    # Handle 0 and nan
    if num == 0:
        return 0
    if np.isnan(num):
        return np.nan

    # Calculate the factor to shift the decimal point
    shift_factor = np.power(10, sig_figs - np.ceil(np.log10(abs(num))))

    # Shift number, round, and shift back
    return round(num * shift_factor) / shift_factor


def derivate_dataframe(df, column):
    """
       Add a column to a dataframe that is the discrete derivative of another column

       Parameters:
           df (pandas.DataFrame): dataframe to apply the function
           column (str): The name of the column from which to calculate the derivative

       Returns:
           pandas.DataFrame: The initial dataframe with an additional 'Derivative' column
       """
    # Ensure the DataFrame has the column 'Total Profile (nm)'
    if column not in df.columns:
        raise ValueError(f"The DataFrame must contain a 'f{column}' column.")
    # Calculate point to point derivative
    df['derivative'] = df[column].diff().fillna(0)
    return df


def calc_poly(coefficient_list, x_end, x_start=0, x_step=1):
    """
       Evaluate an n-degree polynomial using Horner's method. Works with arrays, returning P(x) for every x within
       range [x_start, x_end].

       Parameters:
           coefficient_list (list or numpy array): list of coefficients such that list[i] is the i-order coefficient
           x_end (int): end of the x_range on which to evaluate the polynomial
           x_start (int): start of the x_range on which to evaluate the polynomial
           x_step (int): step size of the x_range on which to evaluate the polynomial

       Returns:
           np.array: P(x) for every x within range [x_start, x_end]
       """
    x = np.arange(x_start, x_end, x_step)
    result = np.zeros_like(x, dtype=np.float64)

    for coefficient in reversed(coefficient_list):
        result = result * x + coefficient

    return result


def make_heatmap_from_dataframe(df, values=None, z_min=None, z_max=None, precision=2, plot_title = "", colorbar_title = ""):
    if values is None:
        values = df.columns[2]

    heatmap_data = df.pivot_table(
        index="y_pos (mm)",
        columns="x_pos (mm)",
        values=values,
    )

    if z_min is None:
        z_min = np.nanmin(heatmap_data.values)
    if z_max is None:
        z_max = np.nanmax(heatmap_data.values)

    heatmap = go.Heatmap(
        x=heatmap_data.columns,
        y=heatmap_data.index,
        z=heatmap_data.values,
        colorscale="Plasma",
        # Set ticks for the colorbar
        colorbar=colorbar_layout(z_min, z_max, precision, title=colorbar_title),
    )

    # Make and show figure
    fig = go.Figure(data=[heatmap], layout=heatmap_layout(title=plot_title))

    if z_min is not None:
        fig.data[0].update(zmin=z_min)
    if z_max is not None:
        fig.data[0].update(zmax=z_max)

    return fig

def check_group_for_results(hdf5_group):
    for position, position_group in hdf5_group.items():
        if 'results' not in position_group:
            return False
    return True


def get_hdf5_datasets(hdf5_file, dataset_type):
    dataset_list = []
    for dataset, dataset_group in hdf5_file.items():
        if 'HT_type' in dataset_group.attrs:
            if dataset_type == dataset_group.attrs['HT_type']:
                dataset_list.append(dataset)

    return dataset_list


def pairwise(list):
    a = iter(list)
    return zip(a, a)


def save_results_dict_to_hdf5(hdf5_results_group, results_dict):
    for key, value in results_dict.items():
        if isinstance(value, dict):
            # Create a group and recurse
            subgroup = hdf5_results_group.create_group(key)
            save_results_dict_to_hdf5(subgroup, value)
        else:
            if isinstance(value, (int, float, str, np.ndarray, list, tuple)):
                hdf5_results_group.create_dataset(key, data=value)
            else:
                # Fallback: store as string representation
                hdf5_results_group.create_dataset(key, data=str(value))


def get_target_position_group(measurement_group, target_x, target_y):
    for position, position_group in measurement_group.items():
        instrument_group = position_group.get("instrument")
        if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
            return position_group


def abs_mean(value_list):
    return np.mean(np.abs(value_list))


def hdf5_group_to_dict(hdf5_group):
    """
    Recursively converts a h5py.Group into a nested dictionary.
    Datasets are read into memory.
    """
    nested_dict = {}

    for key, item in hdf5_group.items():
        if isinstance(item, h5py.Dataset):
            nested_dict[key] = item[()]
        elif isinstance(item, h5py.Group):
            nested_dict[key] = hdf5_group_to_dict(item)

    return nested_dict


def convert_bytes(target):
    try:
        return float(target)
    except ValueError:
        return target.decode('utf-8')




