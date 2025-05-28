from pathlib import Path

import h5py

from ..functions.functions_hdf5 import *


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


def rename_group(group, old_name, new_name):
    """
    Renames a dataset (or subgroup) inside a given group.

    Parameters:
        group     : h5py.Group — the parent group
        old_name  : str        — name of the dataset to rename (relative to group)
        new_name  : str        — new name to assign within the same group
    """
    if new_name in group:
        raise ValueError(f"Cannot rename: '{new_name}' already exists in group '{group.name}'.")

    group.copy(old_name, new_name)
    del group[old_name]


def safe_create_new_subgroup(group, new_subgroup_name):
    """
        If subgroup doesn't exist, create a new subgroup. Returns subgroup.
        Useful to avoid group already exists errors

        Parameters:
            group (h5py.Group) : The parent group
            new_subgroup_name(str) : The name of the new subgroup

        Returns:
            h5py.Group: The new subgroup
    """
    if new_subgroup_name not in group:
        new_subgroup = group.create_group(new_subgroup_name)
    else:
        new_subgroup = group[new_subgroup_name]
    return new_subgroup


def create_incremental_group(hdf5_file, base_name):
    """
    Creates a group with a base name and auto-incrementing index if it already exists.

    Parameters:
    - hdf5_file (h5py.File): An open h5py File object
    - base_name (str): The base name for the group

    Returns:
        h5py.Group: Created subgroup
    """
    index = 1
    group_name = f"{base_name}_{index}"
    while group_name in hdf5_file:
        index += 1
        group_name = f"{base_name}_{index}"
    return hdf5_file.create_group(group_name)


def create_new_hdf5(hdf5_path, sample_metadata):
    """
    Creates a new HDF5 file with the structure for an HT experiment.

    Args:
        hdf5_path (str or Path): The path to the HDF5 file to be created.
        sample_metadata (dict): A dictionary containing metadata for the sample.

    Returns:
        None
    """
    with h5py.File(hdf5_path, "x") as hdf5_file:
        hdf5_file.attrs["HT_class"] = "HTroot"

        sample = hdf5_file.create_group("sample")
        sample.attrs["HT_class"] = "sample"
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

        return True