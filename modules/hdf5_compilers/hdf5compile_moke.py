"""
Functions for MOKE parsing
"""

from hdf5compile_base import *

def get_scan_number(filename):
    """
    Returns the scan number from the given filepath.

    The scan number is stored in the filename of the given filepath
    as 'pN_X_Y_magnetization.txt', where N is the scan number, X and Y are
    the wafer positions.

    Parameters
    ----------
    filepath : str
        The filepath to the MOKE data file (.txt)

    Returns
    -------
    str
        A string containing the scan number.
    """
    scan_number = filename.split("_")[0].replace("p", "")

    return scan_number

def get_wafer_positions(filename):
    """
    Returns the wafer positions (x and y indices) from the given filepath.

    The wafer positions are stored in the filename of the given filepath
    as 'pN_XxYy_magnetization.txt', where N is the scan number, X and Y are
    the wafer positions.

    Parameters
    ----------
    filepath : str
        The filepath to the MOKE data file (.txt)

    Returns
    -------
    tuple
        A tuple containing the x and y wafer positions.
    """
    x_pos = filename.split("_")[1].split("x")[-1]
    y_pos = filename.split("_")[2].split("y")[-1]

    return x_pos, y_pos


def read_header_from_moke(file_string):
    """
    Reads the header information from a MOKE data info file and returns it as a dictionary.

    Parameters
    ----------
    filepath : str or Path
        The filepath to the directory containing the MOKE data file and info.txt.

    Returns
    -------
    dict
        A dictionary containing the header information with keys like "Sample name", "Date", etc.
    """

    header_dict = {}

    with open(file_string, "r", encoding="iso-8859-1") as file:
        header_dict["Sample name"] = file.readline().strip().replace("#", "")
        header_dict["Date"] = file.readline().strip().replace("#", "")
        for line in file:
            key, value = line.strip().split("=")
            header_dict[key] = value

    return header_dict


def read_data_from_moke(filepath):
    """
    Reads data from a MOKE data file and its associated pulse and sum data files.

    Parameters
    ----------
    filepath : str or Path
        The filepath to the MOKE data file.

    Returns
    -------
    tuple
        A tuple containing three lists: magnetization data, pulse data, and sum data. Each list contains the data of the corresponding file.
    """
    mag_data, pul_data, sum_data = [], [], []
    loop_data = []

    mag_path = filepath
    pul_path = filepath.parent / f"{filepath.name.replace('magnetization', 'pulse')}"
    sum_path = filepath.parent / f"{filepath.name.replace('magnetization', 'sum')}"
    loop_path = filepath.parent / f"{filepath.name.replace('magnetization', 'loop')}"

    # Open the 4 datafiles at the same time and write everything in lists
    with open(mag_path, "r") as magnetization, open(pul_path, "r") as pulse, open(
        sum_path, "r"
    ) as reflectivity:

        magnetization = magnetization.readlines()
        pulse = pulse.readlines()
        reflectivity = reflectivity.readlines()

        for mag, pul, sum in zip(magnetization[2:], pulse[2:], reflectivity[2:]):
            mag = mag.strip().split()
            pul = pul.strip().split()
            sum = sum.strip().split()

            mag_data.append([float(elm) for elm in mag])
            pul_data.append([float(elm) for elm in pul])
            sum_data.append([float(elm) for elm in sum])

    # Reading the loop MOKE file
    with open(loop_path, "r") as loop:
        loop = loop.readlines()
        for line in loop[2:]:
            loop_line = line.strip().split()
            loop_data.append([float(elm) for elm in loop_line])

    return mag_data, pul_data, sum_data, loop_data


def get_time_from_moke(datasize):
    """
    Generates a list of time values based on the given data size.

    Parameters
    ----------
    datasize : int
        The number of time steps to generate.

    Returns
    -------
    list
        A list of time values in microseconds, each separated by a time step of 0.05 microseconds.
    """

    time_step = 0.05  # in microsecondes (or 50ns)
    time = [j * time_step for j in range(datasize)]

    return time


def get_results_from_moke(filepath, x_pos_wafer, y_pos_wafer):
    """
    Reads the results of a MOKE measurement from a results file and returns the coercivity and reflectivity values for the given wafer positions.

    Parameters
    ----------
    filepath : str or Path
        The filepath to the MOKE data file.
    x_pos_wafer : int
        The x position of the wafer.
    y_pos_wafer : int
        The y position of the wafer.

    Returns
    -------
    dict
        A dictionary containing the coercivity and reflectivity values for the given wafer positions.
    """
    results_dict = {}
    result_path = None
    # Check if there is a results file
    for file in os.listdir(filepath.parent):
        if file.endswith("MOKE.dat"):
            result_path = filepath.parent / file
            break

    if result_path is None:
        return results_dict
    else:
        with open(result_path, "r") as file:
            file.readline()
            for line in file:
                x, y, coercivity, reflectivity = line.strip().split()
                if float(x) == float(x_pos_wafer) and float(y) == float(y_pos_wafer):
                    results_dict["coercivity"] = round(float(coercivity), 2)
                    results_dict["reflectivity"] = round(float(reflectivity), 2)
                    break

    return results_dict


def set_instrument_from_dict(moke_dict, node):
    """
    Writes the contents of the moke_dict dictionary to the HDF5 node.

    Args:
        moke_dict (dict): A dictionary containing the MOKE data and metadata, generated by the read_header_from_moke and read_data_from_moke functions.
        node (h5py.Group): The HDF5 group to write the data to.
    Returns:
        None
    """
    for key, value in moke_dict.items():
        if isinstance(value, dict):
            set_instrument_from_dict(value, node.create_group(key))
        else:
            node[key] = value

    return None


def write_moke_to_hdf5(HDF5_path, file_name, file_string, mode="a"):
    """
    Writes the contents of the MOKE data file (.txt) to the given HDF5 file.

    Args:
        HDF5_path (str or Path): The path to the HDF5 file to write the data to.
        filepath (str or Path): The path to the MOKE data file (.txt).
        mode (str, optional): The mode to open the HDF5 file in. Defaults to "a".

    Returns:
        None
    """
    scan_number = get_scan_number(filepath)
    x_pos, y_pos = get_wafer_positions(filepath)

    header_dict = read_header_from_moke(filepath)
    mag_dict, pul_dict, sum_dict, loop_dict = read_data_from_moke(filepath)
    time_dict = get_time_from_moke(len(mag_dict))
    nb_aquisitions = len(mag_dict[0])

    results_dict = get_results_from_moke(filepath, x_pos, y_pos)

    with h5py.File(HDF5_path, mode) as f:
        scan_group = f"/entry/moke/scan_{scan_number}/"
        scan = f.create_group(scan_group)

        # Instrument group for metadata
        instrument = scan.create_group("instrument")
        instrument.attrs["NX_class"] = "HTinstrument"
        instrument["x_pos"] = convertFloat(x_pos)
        instrument["y_pos"] = convertFloat(y_pos)
        instrument["x_pos"].attrs["units"] = "mm"
        instrument["y_pos"].attrs["units"] = "mm"

        set_instrument_from_dict(header_dict, instrument)

        # Data group
        data = scan.create_group("measurement")
        data.attrs["NX_class"] = "HTmeasurement"
        time = [convertFloat(t) for t in time_dict]
        time_node = data.create_dataset("time", data=time, dtype="float")
        time_node.attrs["units"] = "μm"

        for i in range(nb_aquisitions):
            mag = [convertFloat(t[i]) for t in mag_dict]
            mag_node = data.create_dataset(
                f"magnetization_{i+1}", data=mag, dtype="float"
            )

            pul = [convertFloat(t[i]) for t in pul_dict]
            pul_node = data.create_dataset(f"pulse_{i+1}", data=pul, dtype="float")

            sum = [convertFloat(t[i]) for t in sum_dict]
            sum_node = data.create_dataset(
                f"reflectivity_{i+1}", data=sum, dtype="float"
            )

            mag_node.attrs["units"] = "V"
            pul_node.attrs["units"] = "V"
            sum_node.attrs["units"] = "V"

        # Results group
        results = scan.create_group("results")
        results.attrs["NX_class"] = "HTresults"
        set_instrument_from_dict(results_dict, results)
        for key in results.keys():
            if key == "coercivity":
                results[key].attrs["units"] = "T"
            elif key == "reflectivity":
                results[key].attrs["units"] = "V"

        applied_field = []
        magnetization = []
        for field, mag in loop_dict:
            applied_field.append(float(field))
            magnetization.append(float(mag))
        applied_field = results.create_dataset(
            "applied field", data=applied_field, dtype="float"
        )
        magnetization = results.create_dataset(
            "magnetization", data=magnetization, dtype="float"
        )
        applied_field.attrs["units"] = "T"
        magnetization.attrs["units"] = "V"
