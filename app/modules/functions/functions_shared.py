import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime


def get_version(tag):
    """
    Scan the versions.txt file to extract version information.

    Parameters:
        tag (str): 'app', 'dektak', 'moke' Select which version to extract

    Returns:
        version (str): version of selected item
    """

    version_file_path = Path("app/config", "versions.txt")
    with open(version_file_path, "r") as version_file:
        for line in version_file:
            try:
                if line.startswith(tag):
                    version = line.split("=")[1].strip()
            except TypeError:
                return None

    return version


def get_database_path(folderpath):
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


def save_with_metadata(df, export_path, metadata=None):
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
        metadata = []

    with open(export_path, "w") as file:
        for line in metadata:
            file.write(f"# {line}\n")

    df.to_csv(export_path, mode="a", index=False)


def read_metadata(database_path):
    """
    For a given database path, read the metadata in the file, as marked by (#) tags

    Parameters:
        database_path (pathlib.Path): Path to the database file

    Returns:
        metadata (list): Metadata extracted from the database
    """

    metadata = []
    with open(database_path, "r") as file:
        for line in file:
            if line.startswith("#"):
                metadata.append(line.strip("#").strip("\n"))

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
        title=title,
        titlefont=dict(size=20),
        xaxis=dict(title="X (mm)", tickfont=dict(size=15), titlefont=dict(size=18)),
        yaxis=dict(title="Y (mm)", tickfont=dict(size=15), titlefont=dict(size=18)),
        height=750,
        width=750,
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


def colorbar_layout(z_min, z_max, title=""):
    """
    Generates a standardized colorbar.

    Parameters:
        z_min : minimum value on the colorbar
        z_max : maximum value on the colorbar
        title (str): The title of the plot.

    Returns:
        colorbar (dict): dictionary of colorbar parameters that can be passed to a figure
    """

    z_mid = (z_min + z_max) / 2
    colorbar = dict(
        title=f"{title} <br>&nbsp;<br>",
        tickfont=dict(size=15),
        titlefont=dict(size=18),
        tickvals=[
            z_min,
            (z_min + z_mid) / 2,
            z_mid,
            (z_max + z_mid) / 2,
            z_max,
        ],  # Tick values
        ticktext=[
            f"{z_min:.2f}",
            f"{(z_min + z_mid) / 2:.2f}",
            f"{z_mid:.2f}",
            f"{(z_max + z_mid) / 2:.2f}",
            f"{z_max:.2f}",
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
    shift_factor = np.pow(10, sig_figs - np.ceil(np.log10(abs(num))))

    # Shift number, round, and shift back
    return round(num * shift_factor) / shift_factor
