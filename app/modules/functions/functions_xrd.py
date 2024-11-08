"""
Functions used in MOKE interactive plot using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import pandas as pd
import os
import pathlib
import numpy as np
import plotly.graph_objects as go

from ..functions.functions_shared import *


def create_coordinate_map(folderpath, prefix="Areamap", suffix=".ras"):
    """
    Create a list of coordinates from the filenames in folderpath.

    This function opens each file in folderpath and reads  the first two coordinates (X and Y) from the file.
    It does this by looking for the lines that start with "*MEAS_COND_AXIS_POSITION-6" and "*MEAS_COND_AXIS_POSITION-7" in the header

    Returns
    -------
    list
        A list of coordinates. Each coordinate is a list with two elements: [X, Y].
    """
    filelist = [
        file
        for file in os.listdir(folderpath)
        if file.endswith(suffix) and file.startswith(prefix)
    ]
    pos_list = []

    for file in filelist:
        file_path = folderpath.joinpath(file)
        with open(file_path, "r", encoding="iso-8859-1") as f:
            for line in f:
                if line.startswith("*MEAS_COND_AXIS_POSITION-6"):
                    x_pos = float(line.split(" ")[1].split('"')[1])
                elif line.startswith("*MEAS_COND_AXIS_POSITION-7"):
                    y_pos = float(line.split(" ")[1].split('"')[1])
                    break
            pos_list.append([x_pos, y_pos, file])
    return pos_list


def plot_xrd_pattern(foldername, datatype, options, xrd_filename, x_pos, y_pos):
    """
    Read an XRD pattern file and return a figure object.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    datatype : str
        Type of data to plot. default is raw XRD data.
    xrd_filename : str
        Name of the XRD data file.
    x_pos : int
        x position of the data file, used for plot title.
    y_pos : int
        y position of the data file, used for plot title.
    xrd_path : str, optional
        Path to the folder containing the XRD data files. Defaults to "./data/XRD/".

    Returns
    -------
    fig : plotly.graph_objects.Figure
        A figure object containing a Scatter plot of the XRD data.
    """
    marker_colors = ["green", "red", "blue", "orange", "purple", "pink", "yellow"]
    names = (
        ["Counts", "Calculated", "Background"]
        + [option for option in options if option.startswith("Q")]
        + ["Amorphous Ta"]
    )

    empty_fig = go.Figure(data=go.Heatmap())
    empty_fig.update_layout(height=600, width=600)
    if foldername is None:
        return empty_fig

    # print(datatype, xrd_filename)
    fullpath = foldername + "/" + xrd_filename
    xrd_data = []
    error = go.Scatter()

    if datatype == "Raw XRD data":
        try:
            with open(fullpath, "r", encoding="iso-8859-1") as file:
                for line in file:
                    if not line.startswith("*"):
                        theta, counts, error = line.split()
                        xrd_data.append([float(theta), float(counts)])

        except FileNotFoundError:
            print(f"{fullpath} ras file not found !")
            return empty_fig

    else:
        fullpath = fullpath.replace(".ras", ".dia")
        try:
            with open(fullpath, "r", encoding="iso-8859-1") as file:
                file_header = next(file)
                for line in file:
                    data_line = line.split()
                    xrd_data.append([float(elm) for elm in data_line])

        except FileNotFoundError:
            print(f"{fullpath} dia file not found !")
            return empty_fig

    xrd_data = np.array(xrd_data)
    fig = go.Figure(
        data=[
            go.Scatter(
                x=[x for x in xrd_data[:, 0]],
                y=[y for y in xrd_data[:, i + 1]],
                marker_color=marker_colors[i],
                name=names[i],
            )
            for i in range(xrd_data.shape[1] - 1)
        ]
    )
    if datatype != "Raw XRD data":
        error = go.Scatter(
            x=xrd_data[:, 0],
            y=[
                (exp - calc) - 2000 for exp, calc in zip(xrd_data[:, 1], xrd_data[:, 2])
            ],
            marker_color="gray",
            name="Error",
        )
        fig.add_trace(error)

    return fig


def read_xrd_files(foldername):
    """
    Read all XRD data files from the given foldername and return the coordinates and filenames as three separate lists.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    xrd_path : str, optional
        Path to the folder containing the XRD data files. Defaults to "./data/XRD/".

    Returns
    -------
    x_pos : list
        List of x coordinates of the data files.
    y_pos : list
        List of y coordinates of the data files.
    xrd_filename : list
        List of filenames of the XRD data files.
    """
    fullpath = pathlib.Path(foldername)
    pos_list = create_coordinate_map(fullpath)

    x_pos = [pos[0] for pos in pos_list]
    y_pos = [pos[1] for pos in pos_list]
    xrd_filename = [pos[2] for pos in pos_list]

    return x_pos, y_pos, xrd_filename


def read_from_lst(lst_file_path, x_pos, y_pos):
    """
    Reads the .lst file from a refinement and returns the header and refined lattice parameters of every phases

    Parameters
    ----------
    lst_file_path : str
        Path to the .lst file.
    x_pos : int
        x position of the data file.
    y_pos : int
        y position of the data file.

    Returns
    -------
    header_lst : str
        The header string containing all the column names.
    DATA_RR_OUTPUT : list
        List containing the position, lattice parameters, and their errors.
    FIT_RR_OUTPUT : list
        List containing the refinement results (R factors, phase name, lattice parameters and their errors).
    """

    with open(lst_file_path, "r") as file:
        header_lst = ["x_pos", "y_pos"]
        phases = []

        DATA_RR_OUTPUT = [x_pos, y_pos]
        FIT_RR_OUTPUT = []

        # reading the .lst file line by line to get lattice parameters
        current_phase = None
        for line in file:
            if line.startswith("Rp="):
                R_factors = line.split("  ")[-1].split(" ")
                for elm in R_factors:
                    FIT_RR_OUTPUT.append(elm.strip())
            elif line.startswith("Local parameters and GOALs for phase"):
                current_phase = line.split()[-1]
                # phases.append(current_phase)
                # name of the current phase for the refined lattice parameters
                FIT_RR_OUTPUT.append(current_phase)
            elif (
                line.startswith("A=") or line.startswith("C=") or line.startswith("B=")
            ):
                FIT_RR_OUTPUT.append(line.strip())
                line_lattice = line.rstrip().split("=")
                # the line is in this format 'C=1.234567+-0.001234' and we split it to only get the value and err
                letter = line_lattice[0]
                if line_lattice[1] == "UNDEF":
                    line_lattice[1] = None
                if "+-" in line:
                    lattice = line_lattice[1].split("+-")
                else:
                    lattice = [line_lattice[1], "0.000000"]
                header_lst += [
                    f"{current_phase}_{letter}",
                    f"{current_phase}_{letter}_err",
                ]
                # adding the column name to the header
                DATA_RR_OUTPUT.append(lattice[0])
                DATA_RR_OUTPUT.append(lattice[1].rstrip())

            # extracting volume fractions now (but is actually found first in the .lst file)

            # same stuff, getting volume fraction values, format can be 'QNd2Fe14B=0.456789' for example
            elif line.startswith("Q"):
                elmt = (line.split("=")[0].strip()).split("Q")[-1]
                FIT_RR_OUTPUT.append(line.strip())
                if "+-" in line:
                    fraction = line.split("=")[1].split("+-")
                else:
                    fraction = [line.split("=")[1].rstrip(), "0.000000"]
                header_lst += [f"Q{elmt}", f"Q{elmt}_err"]

                DATA_RR_OUTPUT.append(fraction[0])
                DATA_RR_OUTPUT.append(fraction[1].rstrip())
    return header_lst, DATA_RR_OUTPUT, FIT_RR_OUTPUT


def save_refinement_results(foldername, header, rr_output):
    """
    Save the refinement results in a file named <foldername>_RR_maps.dat in the result_xrd_path folder.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    result_xrd_path : str
        Path to the folder containing the refinement results files.
    header : str
        The header string containing all the column names.
    rr_output : list
        List containing the refinement results (R factors, phase name, lattice parameters and their errors).
    """
    foldername = pathlib.Path(foldername)
    database = pd.DataFrame()
    database_path = f"{foldername}/{foldername.name}_database.csv"

    for i, line in enumerate(rr_output):
        for j, elm in enumerate(header):
            database.loc[i, elm] = line[j]

    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    app_version = get_version("app")
    database_version = get_version("xrd")

    metadata = [
        f"Date of fitting: {date}",
        f"Code version: {app_version}",
        f"Database type: XRD",
        f"XRD database version = {database_version}",
    ]

    save_with_metadata(database, database_path, metadata=metadata)


def result_file_exists(foldername):
    """
    Check if the refinement results file exists in the result_xrd_path folder.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    result_xrd_path : str
        Path to the folder containing the refinement results files.

    Returns
    -------
    bool
        True if the refinement results file exists, False otherwise.
    """
    foldername = pathlib.Path(foldername)
    save_result = pathlib.Path(f"{foldername}/{foldername.name}_database.csv")

    return save_result.name in os.listdir(foldername)


def get_refinement_results(foldername):
    """
    Read the refinement results files and return the header.

    If the refinement results file does not exist in the result_xrd_path folder,
    it will read the .lst files, get the refined lattice parameters and save them in the result_xrd_path folder.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    xrd_path : str, optional
        Path to the folder containing the XRD data files. Defaults to "./data/XRD/".
    result_xrd_path : str, optional
        Path to the folder containing the refinement results files. Defaults to "./results/XRD/".

    Returns
    -------
    list
        List containing the header of the refinement results file.
    """
    foldername = pathlib.Path(foldername)

    if not result_file_exists(foldername):
        save_list = []
        x_pos, y_pos, xrd_filename = read_xrd_files(foldername)

        for i, ras_file in enumerate(xrd_filename):
            lst_file_path = foldername / ras_file.replace(".ras", ".lst")
            # Read the .lst file and get the refined lattice parameters
            header, rr_output = read_from_lst(lst_file_path, x_pos[i], y_pos[i])[0:2]
            if np.abs(x_pos[i]) + np.abs(y_pos[i]) <= 60:
                save_list.append(rr_output)

        save_refinement_results(foldername, header, save_list)
    else:
        # print("Refinement results file already exists")
        pass

    read_result_file = f"{foldername}/{foldername.name}_database.csv"
    database = pd.read_csv(read_result_file, comment="#")

    header = list(database.columns)

    return header


def get_refined_parameter(foldername, datatype):
    """
    Read the refinement results files and return the coordinates and refined lattice parameters values.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    datatype : str
        Type of data to plot. default, plot raw XRD data.
    result_xrd_path : str
        Path to the folder containing the refinement results files.

    Returns
    -------
    x_pos, y_pos, z_values : list
        List containing the x and y coordinates of the data files and the refined lattice parameters values.
    """
    foldername = pathlib.Path(foldername)
    database_path = pathlib.Path(f"{foldername}/{foldername.name}_database.csv")
    x_pos, y_pos, z_values = [], [], []

    if datatype != "Raw XRD data" and datatype is not None:
        options = get_refinement_results(foldername)
        if datatype in options:
            data = pd.read_csv(database_path, comment="#")
            header = list(data.columns)

            x_pos = data["x_pos"]
            y_pos = data["y_pos"]
            z_values = data[datatype]

            return x_pos, y_pos, z_values

    return None


def check_xrd_refinement(foldername):
    """
    Check if the refinement files (.lst) exist in the given foldername.

    Parameters
    ----------
    foldername : str
        Path to the folder containing the refinement files.
    xrd_path : str, optional
        Path to the folder containing the data files. Defaults to "./data/XRD/".

    Returns
    -------
    bool
        True if refinement files are found, False otherwise.
    """
    foldername = pathlib.Path(foldername)

    # Check if folder exists
    try:
        os.listdir(foldername)
    except FileNotFoundError:
        return False

    # Check if refinement files exist
    lst_files = [file for file in os.listdir(foldername) if file.endswith(".lst")]
    if len(lst_files) > 0:
        options = get_refinement_results(foldername)[2:]
        return options

    return False


def plot_xrd_heatmap(foldername, datatype):
    """
    Plot a heatmap of XRD data.

    Parameters
    ----------
    foldername : str
        Name of the folder containing the XRD data files.
    datatype : str
        Type of data to plot. default, plot raw XRD data.
    xrd_path : str, optional
        Path to the folder containing the XRD data files. Defaults to "./data/XRD/".
    result_xrd_path : str, optional
        Path to the folder containing the results. Defaults to "./results/XRD/".

    Returns
    -------
    fig : plotly.graph_objects.Figure
        A figure object containing a Heatmap plot of the XRD data.
    """

    empty_fig = go.Figure(data=go.Heatmap())
    empty_fig.update_layout(height=600, width=600)
    if foldername is None:
        return empty_fig

    x_pos_file, y_pos_file, xrd_filename = read_xrd_files(foldername)
    coordinate_list = [[x, y] for x, y in zip(x_pos_file, y_pos_file)]

    if datatype is None or datatype == "Raw XRD data":
        z_values = np.zeros(len(x_pos_file) + len(y_pos_file))
    else:
        x_pos, y_pos, z_values = get_refined_parameter(foldername, datatype)
        coordinate_list = [[x, y] for x, y in zip(x_pos, y_pos)]
        filename_list = []
        for i, filename in enumerate(xrd_filename):
            try:
                coordinate_list.index([x_pos_file[i], y_pos_file[i]])
                filename_list.append(filename)
            except ValueError:
                continue

        xrd_filename = filename_list

        # Check if the function did find the refined parameters file.
        if z_values is None:
            return empty_fig
        elif datatype.startswith("Q"):
            # To have the result in %
            z_values = [zs * 100 for zs in z_values]
        else:
            # To have the result in A
            z_values = [zs * 10 for zs in z_values]

    fig = go.Figure(
        data=go.Heatmap(
            x=[coord[0] for coord in coordinate_list],
            y=[coord[1] for coord in coordinate_list],
            z=z_values,
            text=xrd_filename,
            colorscale="Jet",
        )
    )
    fig.update_layout(title=f"XRD map for {foldername}")

    z_min = min(z_values)
    z_max = max(z_values)

    return fig, z_min, z_max
