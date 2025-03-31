import os.path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import h5py
from datetime import datetime


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


def is_macos_system_file(file_path):
    if '/._' not in file_path and not file_path.startswith('._'):
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
        "XRD": ["ras"],
        "MOKE": ["txt"],
        "EDX": ["spx"],
        "PROFIL": ["asc2d"],
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
        sample_group = f['entry/sample']

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