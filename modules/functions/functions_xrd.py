"""
Functions used in XRD interactive plot using Dash.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: Pierre Le Berre - Institut Néel (pierre.le-berre@neel.cnrs.fr)
"""

from ..functions.functions_shared import *

def xrd_conditions(hdf5_path, *args, **kwargs):
    if hdf5_path is None:
        return False
    if not h5py.is_hdf5(hdf5_path):
        return False
    with h5py.File(hdf5_path, "r") as hdf5_file:
        dataset_list = get_hdf5_datasets(hdf5_file, dataset_type="esrf")
        if len(dataset_list) == 0:
            return False
    return True


def xrd_get_integrated_from_hdf5(xrd_group, target_x, target_y):
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    measurement_group = position_group.get("measurement")

    integrated_group = measurement_group.get(["CdTe_integrate"])

    q_array = integrated_group['q'][()]
    intensity_array = integrated_group['intensity'][()]

    measurement_dataframe = pd.DataFrame({"q": q_array, "intensity": intensity_array})

    return measurement_dataframe


def xrd_get_image_from_hdf5(xrd_group, target_x, target_y):
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    measurement_group = position_group.get("measurement")

    image_array = measurement_group['CdTe'][()]

    return image_array


def xrd_get_results_from_hdf5(xrd_group, target_x, target_y):
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    results_group = position_group.get("results")
    if results_group is None:
        raise KeyError("results group not found in file")
    data_dict = hdf5_group_to_dict(results_group)
    return data_dict


def xrd_make_results_dataframe_from_hdf5(xrd_group):
    data_dict_list = []

    for position, position_group in xrd_group.items():
        instrument_group = position_group.get("instrument")
        # Exclude spots outside the wafer
        if np.abs(instrument_group["x_pos"][()]) + np.abs(instrument_group["y_pos"][()]) <= 60:

            results_group = position_group.get("results")

            data_dict = {"x_pos (mm)": instrument_group["x_pos"][()], "y_pos (mm)": instrument_group["y_pos"][()]}

            if results_group is None:
                continue

            for value, value_group in results_group.items():
                if "units" in value_group.attrs:
                    units = value_group.attrs["units"]
                else:
                    units = "arb"
                data_dict[f"{value}_({units})"] = value_group[()]
            data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe