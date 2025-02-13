from pathlib import Path
import h5py
import xml.etree.ElementTree as et
import pathlib
import h5py
import numpy as np
import re


def detect_measurement(filename_list: list):
    """
       Scan a folder to determine which type of measurement it is

       Parameters:
           filename_list (list): list containing all filenames to parse

       Returns:
           version (str): detected measurement type
       """
    measurement_dict = {
        "MOKE": ["txt", "log", "csv"],
        "EDX": ["spx", "xlsx", "rtj2"],
        "DEKTAK": ["asc2d", "csv"],
        "XRD": ["ras", "raw", "asc", "img", "pdf"],
    }

    for measurement_type, file_type in measurement_dict.items():
        ok = True
        for filename in filename_list:
            if filename.startswith('.'):
                continue
            if filename.split('.')[-1] not in file_type:
                # print(f"Found .{filename.split('.')[-1]} file at odds with {measurement_type} spec")
                ok = False
                break
            if not ok:
                break
        if ok:
            return measurement_type


def convertFloat(item):
    """
    Converts the given item to a float if possible.

    Args:
        item: The item to be converted, which can be of any type.

    Returns:
        The item converted to a float if conversion is successful;
        otherwise, returns the item unchanged.
    """
    try:
        item = float(item)
    except (ValueError, TypeError):
        pass

    return item


def get_all_keys(d):
    """
    Recursively yields all keys and values in a nested dictionary.

    Args:
        d (dict): The dictionary to be searched.

    Yields:
        tuple: A tuple containing the key and value of each item in the dictionary.
    """
    for key, value in d.items():
        yield key, value
        if isinstance(value, dict):
            yield from get_all_keys(value)


def create_multiple_groups(hdf5_node, group_list):
    """
    Creates multiple groups in a HDF5 file. Also sets the NX_class attribute for each group.
    The NX_class attribute is used to identify the type of the group.

    Args:
        hdf5_node (h5py.Group): The node of the HDF5 file where the groups should be created.
        group_list (list[str]): A list of strings containing the names of the groups to be created.

    Returns:
        list of h5py.Group: A list of groups created in the HDF5 file.
    """
    node_list = []

    for group in group_list:
        nxgroup = hdf5_node.create_group(group)
        nxgroup.attrs["NX_class"] = f"HT{group}"
        node_list.append(nxgroup)

    return node_list


def create_new_hdf5(hdf5_path, sample_metadata):
    """
    Creates a new HDF5 file with the structure for a HT experiment.

    Args:
        hdf5_path (str or Path): The path to the HDF5 file to be created.
        sample_metadata (dict): A dictionary containing metadata for the sample.

    Returns:
        None
    """
    with h5py.File(hdf5_path, "w") as f:
        f.attrs["default"] = "entry"
        f.attrs["NX_class"] = "HTroot"

        htentry = f.create_group("entry")
        htentry.attrs["NX_class"] = "HTentry"
        htentry.attrs["default"] = "edx"

        sample = htentry.create_group("sample")
        sample.attrs["NX_class"] = "HTsample"
        current_group = sample
        counts = 0
        for key, value in get_all_keys(sample_metadata):
            if isinstance(value, dict):
                counts = len(value)
                current_group = current_group.create_group(key)
            else:
                current_group[key] = convertFloat(value)
                counts -= 1
                if counts <= 0:
                    current_group = sample
                    counts = 0

        create_multiple_groups(htentry, ["edx", "moke", "xrd"])

    return None



def visit_items(item, edx_dict={}):
    """
    Recursively visits XML elements to build a nested dictionary representation.

    This function processes an XML element and its children, forming a hierarchy
    of dictionaries where each key represents an XML tag or type. Elements with
    specific tags listed in `parse_ignore` are skipped. If an element has no
    children, its text is added as a value in the dictionary. Otherwise, the
    function is called recursively to process its children.

    Args:
        item (xml.etree.ElementTree.Element): The XML element to process.
        edx_dict (dict, optional): The dictionary to update with parsed data.
            Defaults to an empty dictionary.

    Returns:
        dict: A nested dictionary representing the structure of the XML elements.
    """
    parse_ignore = [
        "",
        "DetLayers",
        "ShiftData",
        "PPRTData",
        "ResponseFunction",
        "Channels",
        "WindowLayers",
    ]

    # Extract the name of the parent element
    if item.tag == "ClassInstance" and item.attrib["Type"] == "TRTPSEElement":
        parent_name = item.attrib["Type"] + " " + item.attrib["Name"]
    elif item.tag == "Result" or item.tag == "ExtResults":
        for child in item.iter():
            if child.tag == "Atom":
                parent_name = item.tag + " " + child.text
    elif item.tag == "ClassInstance":
        parent_name = item.attrib["Type"]
    else:
        parent_name = item.tag

    # Builds a nested dictionary with all the edx metadata
    edx_dict.update({parent_name: {}})
    for child in item:
        if child.tag in parse_ignore:
            continue
        elif child.findall("./") == []:
            edx_dict[parent_name][child.tag] = child.text
        else:
            # Recursively visit the child elements
            edx_dict = visit_items(child, edx_dict)

    return edx_dict


def get_channels(xml_root):
    """
    Extracts the channel data from an XML root element to a list of counts.

    Args:
        xml_root (xml.etree.ElementTree.Element): The root element of the XML tree.

    Returns:
        list: A list of strings representing the channel data extracted from the XML.
    """
    channels = []

    for elm in xml_root.iter("Channels"):
        channels = [int(counts) for counts in elm.text.split(",")]

    return channels


def read_data_from_spx(file_string: str):
    """
    Reads data from an XML file (.spx) containing EDX data exported from BRUKER instrument.

    Args:
        filepath (str or Path): The path to the XML file to read.

    Returns:
        tuple: A tuple containing a dictionary of metadata and a list of channel counts.
    """
    # Parse the XML file
    root = et.fromstring(file_string)

    # Extract the data and metadata from xml
    edx_dict = visit_items(root)
    channels = get_channels(root)

    return edx_dict, channels


def get_position_from_name(filename: str):
    """
    Extracts the scan numbers (x and y indices) from the filename of the given
    filepath.

    Args:
        filename (str): Name of the file containing position information with the format (x, y)

    Returns:
        tuple: A tuple containing the x and y indices of the scan
    """

    pattern = r'\((\d+),(\d+)\)'
    match = re.search(pattern, filename)
    x_idx = match.group(1)
    y_idx = match.group(2)

    return int(x_idx), int(y_idx)


def calculate_wafer_positions(scan_numbers, step_x=5, step_y=5, start_x=-40, start_y=-40):
    """
    Calculates the wafer positions based on scan numbers and specified step and start values.

    Args:
        scan_numbers (tuple): A tuple containing the x and y indices of the scan.
        step_x (int, optional): The step size in the x direction. Defaults to 5.
        step_y (int, optional): The step size in the y direction. Defaults to 5.
        start_x (int, optional): The starting position in the x direction. Defaults to -40.
        start_y (int, optional): The starting position in the y direction. Defaults to -40.

    Returns:
        tuple: A tuple containing the calculated x and y positions on the wafer.
    """
    x_idx, y_idx = scan_numbers
    x_pos, y_pos = (x_idx - 1) * step_x + start_x, (y_idx - 1) * step_y + start_y

    return x_pos, y_pos


def get_units(key):
    """
    Returns the unit of measurement for a given key.

    Parameters
    ----------
    key : str
        The key to look up in the dictionary.

    Returns
    -------
    str or None
        The unit of measurement associated with the key, or None if key is not found in the dictionary.
    """
    dict_units = {
        "PrimaryEnergy": "keV",
        "WorkingDistance": "mm",
        "CalibAbs": "keV",
        "CalibLin": "keV",
        "DetectorTemperature": "°C",
        "DetectorThickness": "mm",
        "SiDeadLayerThickness": "mm",
        "AtomPercent": "at.%",
        "MassPercent": "mass.%",
    }

    if key in dict_units.keys():
        return dict_units[key]
    return None


def set_instrument_and_result_from_dict(edx_dict, instrument_group, result_group):
    """
    Writes the contents of the edx_dict dictionary to the HDF5 instrument_group and result_group.

    Args:
        edx_dict (dict): A dictionary containing the EDX data and metadata, generated by the visit_items function.
        instrument_group (h5py.Group): The HDF5 group to write the instrument data to.
        result_group (h5py.Group): The HDF5 group to write the result data to.
    Returns:
        None
    """
    for key, value in get_all_keys(edx_dict):
        if isinstance(value, dict):
            if [key for key in value.keys()] == []:
                continue
            elif key.startswith("Result") or key == "TRTResult":
                instrument_subgroup = result_group.create_group(key)
            elif key.startswith("ExtResults"):
                instrument_subgroup = result_group[f"Result {value["Atom"]}"]
                del instrument_subgroup["Atom"]
            elif key.startswith("TRTPSEElement"):
                tmp_group = result_group[f"Result {value["Element"]}"]
                new_key = f"Element {key.replace('TRTPSEElement ', '')}"
                result_group[new_key] = tmp_group
                instrument_subgroup = result_group[new_key]

                # Remove element from result group after name manipulation
                # This has to be done to avoid duplicate in the hdf5 file
                del result_group[f"Result {value["Element"]}"]
                del instrument_subgroup["Atom"]
            else:
                instrument_subgroup = instrument_group.create_group(
                    f"{key}".replace("TRT", "")
                )

            for subkey, subvalue in get_all_keys(value):
                if subvalue is not None:
                    if subkey == "AtomPercent" or subkey == "MassPercent":
                        # Convert values to .%
                        instrument_subgroup[subkey] = convertFloat(subvalue) * 100
                    else:
                        instrument_subgroup[subkey] = convertFloat(subvalue)
                    if get_units(subkey) is not None:
                        instrument_subgroup[subkey].attrs["units"] = get_units(subkey)


def make_energy_dataset(edx_dict, channels):
    """
    Calculates the energy array for the EDX data based on the values in
    the edx_dict dictionary.

    Args:
        edx_dict (dict): A dictionary containing the EDX data and metadata, generated by the visit_items function.
        channels (list): A list of channel counts, generated by the read_data_from_spx function.

    Returns:
        numpy.ndarray: An array of energy values corresponding to the channels.

    Notes:
        The energy calculation is based on the values in the edx_dict dictionary,
        specifically the "CalibAbs" and "CalibLin" values.
    """
    zero_energy = convertFloat(edx_dict["TRTSpectrumHeader"]["CalibAbs"])
    energy_step = convertFloat(edx_dict["TRTSpectrumHeader"]["CalibLin"])

    energy = np.array(
        [((i + 1) * energy_step + zero_energy) for i in range(len(channels) // 2)]
    )

    return energy


def write_edx_to_hdf5(HDF5_path, filename, filestring, mode="a"):
    """
    Writes the contents of the EDX data file (.spx) to the given HDF5 file.

    Args:
        HDF5_path (str or Path): The path to the HDF5 file to write the data to.
        filepath (str or Path): The path to the EDX data file (.spx).
        mode (str, optional): The mode to open the HDF5 file in. Defaults to "a".

    Returns:
        None
    """
    scan_numbers = get_position_from_name(filename)
    wafer_positions = calculate_wafer_positions(scan_numbers)
    edx_dict, channels = read_data_from_spx(filestring)
    energy = make_energy_dataset(edx_dict, channels)

    with h5py.File(HDF5_path, mode) as f:
        scan_group = f"/entry/edx/scan_{scan_numbers[0]},{scan_numbers[1]}/"
        scan = f.create_group(scan_group)

        # Instrument group for metadata
        instrument = scan.create_group("instrument")
        instrument.attrs["NX_class"] = "HTinstrument"

        instrument["x_pos"] = wafer_positions[0]
        instrument["y_pos"] = wafer_positions[1]
        instrument["x_pos"].attrs["units"] = "mm"
        instrument["y_pos"].attrs["units"] = "mm"

        # Result group
        results = scan.create_group("results")
        results.attrs["NX_class"] = "HTresult"
        set_instrument_and_result_from_dict(edx_dict, instrument, results)

        # Measurement group
        data = scan.create_group("measurement")
        data.attrs["NX_class"] = "HTdata"

        counts = data.create_dataset(
            "counts", (len(channels),), data=channels, dtype="int"
        )
        energy = data.create_dataset(
            "energy", (len(energy),), data=energy, dtype="float"
        )
        counts.attrs["units"] = "cps"
        energy.attrs["units"] = "keV"

    return None
