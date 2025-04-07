"""
Functions used in MOKE interactive plot using Dash.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: Pierre Le Berre - Institut Néel (pierre.le-berre@neel.cnrs.fr)
"""
import numpy as np
from plotly.subplots import make_subplots
from scipy.signal import savgol_filter
from collections import defaultdict
import re

from ..functions.functions_shared import *


def check_for_moke(hdf5_path):
    with h5py.File(hdf5_path, "r") as f:
        if "moke" in f["entry"].keys():
            return True
        else:
            return False


def moke_get_measurement_from_hdf5(hdf5_path, target_x, target_y, index=1):
    if not check_for_moke(hdf5_path):
        raise KeyError("Moke not found in file. Please check your file")

    with h5py.File(hdf5_path, "r") as f:
        moke_group = f["/entry/moke"]
        for position, position_group in moke_group.items():
            instrument_group = position_group.get("instrument")
            if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
                measurement_group = position_group.get("measurement")
                shot_group = measurement_group.get(f"shot_{index}")
                if shot_group is None:
                    raise KeyError("Failed to retrieve shot group, index is probably out of bounds")

                kerr_array = shot_group[f"magnetization_{index}"][()]
                pulse_array = shot_group[f"pulse_{index}"][()]
                sum_array = shot_group[f"reflectivity_{index}"][()]
                time_array = measurement_group[f"time"][()]

                measurement_dataframe = pd.DataFrame(
                    {"kerr_rotation": kerr_array, "pulse": pulse_array, "sum": sum_array, "time": time_array})

                return measurement_dataframe



def moke_get_voltage_from_hdf5(hdf5_path, target_x, target_y):
    if not check_for_moke(hdf5_path):
        raise KeyError("Moke not found in file. Please check your file")

    with h5py.File(hdf5_path, "r") as f:
        moke_group = f["/entry/moke"]
        for position, position_group in moke_group.items():
            instrument_group = position_group.get("instrument")
            if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
                pulse_voltage = instrument_group["Pulse_voltage(V)"][()]
                return pulse_voltage



def moke_integrate_pulse_array(pulse_array):
    field_array = np.zeros_like(np.array(pulse_array))

    field_array[350:660] = np.cumsum(pulse_array[350:660])
    field_array[1350:1660] = np.cumsum(pulse_array[1350:1660])

    return field_array

def moke_treat_measurement_dataframe(measurement_df, options_dict):
    # Check compatibility with the provided data treatment dictionary
    try:
        coil_factor = float(options_dict["coil_factor"])
        pulse_voltage = float(options_dict["pulse_voltage"])
        smoothing = options_dict["smoothing"]
        smoothing_polyorder = int(options_dict["smoothing_polyorder"])
        smoothing_range = int(options_dict["smoothing_range"])
        correct_offset = options_dict["correct_offset"]
        filter_zero = options_dict["filter_zero"]
        connect_loops = options_dict["connect_loops"]

    except KeyError:
        raise KeyError(
            "Invalid data treatment dictionary, "
            "check compatibility between callbacks_moke.store_data_treatment and functions_moke.treat_data"
        )
    

    # Set field using coil parameters
    midpoint = len(measurement_df) // 2
    max_field = pulse_voltage * coil_factor / 100

    measurement_df.loc[:midpoint, "Field"] = measurement_df.loc[:midpoint, "Field"].apply(
        lambda x: -x * max_field / np.abs(measurement_df["Field"].min())
    )
    measurement_df.loc[midpoint:, "Field"] = measurement_df.loc[midpoint:, "Field"].apply(
        lambda x: -x * max_field / np.abs(measurement_df["Field"].max())
    )

    # Vertically center the loop
    if correct_offset:
        magnetization_offset = measurement_df["Magnetization"].mean()
        measurement_df.loc[:, "Magnetization"] = measurement_df.loc[:, "Magnetization"].apply(
            lambda x: x - magnetization_offset
        )

    # Remove oddities around H=0 by forcing points in the positive(negative) loop to be over(under) a threshold
    if filter_zero:
        length = len(measurement_df)
        measurement_df = measurement_df[measurement_df["Field"].notna()]

        measurement_df.loc[: length // 2, "Field"] = measurement_df.loc[: length // 2].where(
            measurement_df["Field"] > 1e-2
        )
        measurement_df.loc[length // 2 :, "Field"] = measurement_df.loc[length // 2 :].where(
            measurement_df["Field"] < -1e-2
        )

    # Rearrange loops from (0, +H, 0, -H, 0) to (-H, 0, +H, 0, -H). Enables connection over 0
    if connect_loops:
        max_index = measurement_df["Field"].idxmax()
        min_index = measurement_df["Field"].idxmin()

        descending = measurement_df.loc[max_index:min_index, :]
        ascending = pd.concat((measurement_df.loc[min_index:, :], measurement_df.loc[:max_index, :]))

        measurement_df = pd.concat((descending, ascending))

    # Smoothing
    if smoothing:
        measurement_df.loc[:, "Magnetization"] = savgol_filter(
            measurement_df["Magnetization"], smoothing_range, smoothing_polyorder
        )

    return measurement_df

def moke_calc_max_kerr_rotation(data: pd.DataFrame):
    """
    From a dataframe, return the value for the saturation Kerr rotation

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'Magnetization' column

    Returns:
        float
    """
    try:
        kerr_max = data["Magnetization"].max()
        kerr_min = data["Magnetization"].min()
        kerr_mean = (kerr_max + np.abs(kerr_min)) / 2
        return kerr_mean
    except NameError:
        raise NameError("Magnetization column not defined")


def moke_calc_reflectivity(data: pd.DataFrame):
    """
    From a dataframe, return the value for the reflectivity Kerr rotation

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'Sum' column

    Returns:
        float
    """
    try:
        reflectivity = data["Sum"].mean(axis=0)
        return reflectivity
    except NameError:
        raise NameError("Sum column not defined")


def moke_calc_derivative_coercivity(data: pd.DataFrame):
    """
    From a dataframe, return the field values for the extremes of dM/dH

    Parameters:
       data(pd.Dataframe) : source dataframe with a 'Field' and 'Magnetization' column

    Returns:
       float, float
    """
    data["Derivative"] = data["Magnetization"] - data["Magnetization"].shift(1)
    data.loc[np.abs(data["Field"]) < 2e-3, "Derivative"] = (
        0  # (Avoid derivative discrepancies around 0 Field)
    )

    # For positive / negative field, find index of maximum / minimum derivative and extract corresponding field
    coercivity_positive = data.loc[
        data.loc[data["Field"] > 0, "Derivative"].idxmax(skipna=True), "Field"
    ]
    coercivity_negative = data.loc[
        data.loc[data["Field"] < 0, "Derivative"].idxmin(skipna=True), "Field"
    ]

    return coercivity_positive, coercivity_negative


def moke_calc_mzero_coercivity(data: pd.DataFrame):
    """
    From a dataframe, return the field values where Magnetization is closest to 0

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'Field' and 'Magnetization' column

    Returns:
        float, float
    """
    coercivity_positive = data.loc[
        np.abs(data.loc[data["Field"] > 0, "Magnetization"]).idxmin(skipna=True),
        "Field",
    ]
    coercivity_negative = data.loc[
        np.abs(data.loc[data["Field"] < 0, "Magnetization"]).idxmin(skipna=True),
        "Field",
    ]

    return coercivity_positive, coercivity_negative


def moke_fit_intercept(data: pd.DataFrame, treatment_dict: dict):
    """
    From a dataframe, fit for the intercept field and return the intercept field values

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'Field' and 'Magnetization' column
        treatment_dict(dict) : Dictionary with data treatment information. See callbacks_moke.store_data_treatment

    Returns:
        float, float, dict
        Returned dictionary contains the direct results from the fits for plotting
    """

    force_flat = True

    coil_factor = float(treatment_dict["coil_factor"])
    pulse_voltage = float(treatment_dict["pulse_voltage"])
    max_field = coil_factor / 100 * pulse_voltage

    sat_field = 1.75  # Should be a data treatment variable, WIP

    Hmin = 0.1
    Hmax = sat_field - 0.25
    Hmin_sat = sat_field + 0.25
    Hmax_sat = 0.95 * max_field

    non_nan = data[data["Field"].notna()].index.values

    section = data.loc[non_nan, ("Magnetization", "Field")]
    section.reset_index(drop=True, inplace=True)

    linear_section = section[
        (np.abs(section["Field"]) > Hmin) & (np.abs(section["Field"]) < Hmax)
    ]
    pos_sat_section = section[
        (section["Field"] > Hmin_sat) & (section["Field"] < Hmax_sat)
    ]
    neg_sat_section = section[
        (section["Field"] < -Hmin_sat) & (section["Field"] > -Hmax_sat)
    ]

    # 1: Linear section
    # 2: Positive saturation section
    # 3: Negative saturation section

    x1 = linear_section["Field"].values
    y1 = linear_section["Magnetization"].values
    slope1, intercept1 = np.polyfit(x1, y1, 1)

    x2 = pos_sat_section["Field"].values
    y2 = pos_sat_section["Magnetization"].values
    if force_flat:
        slope2 = 0
        intercept2 = np.polyfit(x2, y2, 0)
    else:
        slope2, intercept2 = np.polyfit(x2, y2, 1)

    x3 = neg_sat_section["Field"].values
    y3 = neg_sat_section["Magnetization"].values
    if force_flat:
        slope3 = 0
        intercept3 = np.polyfit(x3, y3, 0)
    else:
        slope3, intercept3 = np.polyfit(x3, y3, 1)

    positive_intercept_field = (intercept2 - intercept1) / (slope1 - slope2)
    negative_intercept_field = (intercept3 - intercept1) / (slope1 - slope3)

    # Make dictionary with results from the fits, can be used for plotting
    fit_dict = {
        "linear_section": [slope1, intercept1, x1],
        "positive_section": [slope2, intercept2, x2],
        "negative_section": [slope3, intercept3, x3],
    }

    return float(positive_intercept_field), float(negative_intercept_field), fit_dict


def moke_batch_extract_results(hdf5_path, treatment_dict):
    if not check_for_moke(hdf5_path):
        raise KeyError("Moke not found in file. Please check your file")


    with h5py.File(hdf5_path, "r") as hdf5_file:
        moke_group = hdf5_file["moke_group"]
        for position, position_group in moke_group.items():
            measurement_group = position_group.get(["measurement"])

            integrated_pulse_arrays = []
            mag_arrays = []
            reflectivity_arrays = []

            # Iterate over every shot (up to 99), and break once the index is not found
            for i in range(99):
                shot_key = f"shot_{i}"
                if shot_key in measurement_group:
                    shot_group = measurement_group.get([f"shot_{i}"])
                    integrated_pulse_arrays.append(shot_group[f'integrated_pulse_{i}'])
                    mag_arrays.append(shot_group[f'magnetization_{i}'])
                    reflectivity_arrays.append(shot_group[f'reflectivity_{i}'])
                else:
                    break

            mean_integrated_pulse = np.mean(np.stack(integrated_pulse_arrays), axis=0)
            mean_magnetization = np.mean(np.stack(mag_arrays), axis=0)
            mean_reflectivity = np.mean(np.stack(reflectivity_arrays), axis=0)



    return None



















# def extract_loop_section(data: pd.DataFrame):
#     """
#     From a dataframe, select only the parts where the field is defined, resulting in a section containing only the loop
#
#     Parameters:
#         data(pd.Dataframe) : source dataframe with a 'Field' column
#     Returns:
#         pd.Dataframe
#     """
#     # Keep only the points where field is defined, removing points outside of pulse
#     try:
#         non_nan = data[data["Field"].notna()].index.values
#         loop_section = data.loc[non_nan, :]
#         loop_section.reset_index(drop=True, inplace=True)
#         return loop_section
#     except NameError:
#         raise NameError("Field column not defined")