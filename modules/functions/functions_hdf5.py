from pathlib import Path
import h5py


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
                print(f"Found .{filename.split('.')[-1]} file at odds with {measurement_type} spec")
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