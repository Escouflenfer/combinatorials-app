"""
"""
from scipy.signal import savgol_filter

from ..functions.functions_shared import *


def moke_conditions(hdf5_path, *args, **kwargs):
    if hdf5_path is None:
        return False
    if not h5py.is_hdf5(hdf5_path):
        return False
    with h5py.File(hdf5_path, "r") as hdf5_file:
        dataset_list = get_hdf5_datasets(hdf5_file, dataset_type="moke")
        if len(dataset_list) == 0:
            return False
    return True


def moke_get_measurement_from_hdf5(moke_group, target_x, target_y, index=1):
    position_group = get_target_position_group(moke_group, target_x, target_y)
    measurement_group = position_group.get("measurement")
    time_array = measurement_group[f"time"][()]

    if index == 0:
        mean_shot_group = measurement_group.get(["shot_mean"])

        magnetization_array = mean_shot_group["magnetization_mean"][()]
        pulse_array = mean_shot_group["pulse_mean"][()]
        reflectivity_array = mean_shot_group["reflectivity_mean"][()]
        integrated_pulse_array = mean_shot_group["integrated_pulse_mean"][()]

        measurement_dataframe = pd.DataFrame(
            {"magnetization": magnetization_array, "pulse": pulse_array, "reflectivity": reflectivity_array,
             "integrated_pulse": integrated_pulse_array, "time": time_array})

        return measurement_dataframe

    elif index > 0:
        shot_group = measurement_group.get(f"shot_{index}")

        if shot_group is None:
            raise KeyError("Failed to retrieve shot group, index is probably out of bounds")

        magnetization_array = shot_group[f"magnetization_{index}"][()]
        pulse_array = shot_group[f"pulse_{index}"][()]
        reflectivity_array = shot_group[f"reflectivity_{index}"][()]
        integrated_pulse_array = shot_group[f"integrated_pulse_{index}"][()]

        measurement_dataframe = pd.DataFrame(
            {"magnetization": magnetization_array, "pulse": pulse_array, "reflectivity": reflectivity_array,
             "integrated_pulse": integrated_pulse_array, "time": time_array})

        return measurement_dataframe


def moke_get_results_from_hdf5(moke_group, target_x, target_y):
    position_group = get_target_position_group(moke_group, target_x, target_y)
    results_group = position_group.get("results")
    if results_group is None:
        raise KeyError("results group not found in file")
    data_dict = hdf5_group_to_dict(results_group)
    return data_dict


def moke_get_instrument_dict_from_hdf5(moke_group):
    instrument_dict = {}
    
    parameters_group = moke_group.get("scan_parameters")
    for value, value_group in parameters_group.items():
        instrument_dict[value] = convert_bytes(value_group[()])
    
    return instrument_dict

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

    measurement_df.loc[:midpoint, "field"] = measurement_df.loc[:midpoint, "integrated_pulse"].apply(
        lambda x: -x * max_field / np.abs(measurement_df["integrated_pulse"].min())
    )
    measurement_df.loc[midpoint:, "field"] = measurement_df.loc[midpoint:, "integrated_pulse"].apply(
        lambda x: -x * max_field / np.abs(measurement_df["integrated_pulse"].max())
    )

    # Vertically center the loop
    if correct_offset:
        magnetization_offset = measurement_df["magnetization"].mean()
        measurement_df.loc[:, "magnetization"] = measurement_df.loc[:, "magnetization"].apply(
            lambda x: x - magnetization_offset
        )

    # Remove oddities around H=0 by forcing points in the positive(negative) loop to be over(under) a threshold
    if filter_zero:
        length = len(measurement_df)
        measurement_df = measurement_df[measurement_df["field"].notna()]

        measurement_df.loc[: length // 2, "field"] = measurement_df.loc[: length // 2, "field"].where(
            measurement_df["field"] > 1e-2
        )
        measurement_df.loc[length // 2 :, "field"] = measurement_df.loc[length // 2 :, "field"].where(
            measurement_df["field"] < -1e-2
        )

    if connect_loops:
        # Step 1: Remove NaNs (if filtering left them)
        measurement_df = measurement_df[measurement_df["field"].notna()]

        # Step 2: Split into two halves (assuming they're in time order)
        midpoint = len(measurement_df) // 2
        first_pulse = measurement_df.iloc[:midpoint]  # 0 → -X → 0
        second_pulse = measurement_df.iloc[midpoint:]  # 0 → +X → 0

        # Step 3: Rearrange: +X → 0 → -X → 0 → +X (start from end of second pulse)
        reordered = pd.concat([second_pulse, first_pulse], ignore_index=True)

        # Step 4 (optional): Loop continuity — duplicate first few points at end
        wrap_points = 1  # number of points to "wrap"
        if len(reordered) >= wrap_points:
            reordered = pd.concat([reordered, reordered.iloc[:wrap_points]], ignore_index=True)

        measurement_df = reordered

    # Smoothing
    if smoothing:
        measurement_df.loc[:, "magnetization"] = savgol_filter(
            measurement_df["magnetization"], smoothing_range, smoothing_polyorder
        )


    return measurement_df


def extract_loop_section(data: pd.DataFrame):
    """
    From a dataframe, select only the parts where the field is defined, resulting in a section containing only the loop

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'field' column
    Returns:
        pd.Dataframe
    """
    # Keep only the points where field is defined, removing points outside of pulse
    try:
        non_nan = data[data["field"].notna()].index.values
        loop_section = data.loc[non_nan, :]
        loop_section.reset_index(drop=True, inplace=True)
        return loop_section
    except NameError:
        raise NameError("field column not defined")



def moke_calc_max_kerr_rotation(data: pd.DataFrame):
    """
    From a dataframe, return the value for the saturation Kerr rotation

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'magnetization' column

    Returns:
        float
    """
    try:
        kerr_max = data["magnetization"].max()
        kerr_min = data["magnetization"].min()
        kerr_mean = (kerr_max + np.abs(kerr_min)) / 2
        return kerr_mean
    except NameError:
        raise NameError("magnetization column not defined")


def moke_calc_reflectivity(data: pd.DataFrame):
    """
    From a dataframe, return the value for the reflectivity Kerr rotation

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'Sum' column

    Returns:
        float
    """
    try:
        reflectivity = data["reflectivity"].mean(axis=0)
        return reflectivity
    except NameError:
        raise NameError("reflectivity column not defined")


def moke_calc_derivative_coercivity(data: pd.DataFrame):
    """
    From a dataframe, return the field values for the extremes of dM/dH

    Parameters:
       data(pd.Dataframe) : source dataframe with a 'field' and 'magnetization' column

    Returns:
       float, float
    """
    data = derivate_dataframe(data, "magnetization")
    data.loc[np.abs(data["field"]) < 2e-3, "derivative"] = (
        0  # Avoid derivative discrepancies around 0 field
    )

    # For positive / negative field, find index of maximum / minimum derivative and extract corresponding field
    coercivity_positive = data.loc[
        data.loc[data["field"] > 0, "derivative"].idxmax(skipna=True), "field"
    ]
    coercivity_negative = data.loc[
        data.loc[data["field"] < 0, "derivative"].idxmin(skipna=True), "field"
    ]

    return coercivity_positive, coercivity_negative


def moke_calc_mzero_coercivity(data: pd.DataFrame):
    """
    From a dataframe, return the field values where magnetization is closest to 0

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'field' and 'magnetization' column

    Returns:
        float, float
    """
    coercivity_positive = data.loc[
        np.abs(data.loc[data["field"] > 0, "magnetization"]).idxmin(skipna=True),
        "field",
    ]
    coercivity_negative = data.loc[
        np.abs(data.loc[data["field"] < 0, "magnetization"]).idxmin(skipna=True),
        "field",
    ]

    return coercivity_positive, coercivity_negative


def moke_fit_intercept(data: pd.DataFrame, treatment_dict: dict):
    """
    From a dataframe, fit for the intercept field and return the intercept field values

    Parameters:
        data(pd.Dataframe) : source dataframe with a 'field' and 'magnetization' column
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

    non_nan = data[data["field"].notna()].index.values

    section = data.loc[non_nan, ("magnetization", "field")]
    section.reset_index(drop=True, inplace=True)

    linear_section = section[
        (np.abs(section["field"]) > Hmin) & (np.abs(section["field"]) < Hmax)
    ]
    pos_sat_section = section[
        (section["field"] > Hmin_sat) & (section["field"] < Hmax_sat)
    ]
    neg_sat_section = section[
        (section["field"] < -Hmin_sat) & (section["field"] > -Hmax_sat)
    ]

    # 1: Linear section
    # 2: Positive saturation section
    # 3: Negative saturation section

    x1 = linear_section["field"].values
    y1 = linear_section["magnetization"].values
    slope1, intercept1 = np.polyfit(x1, y1, 1)

    x2 = pos_sat_section["field"].values
    y2 = pos_sat_section["magnetization"].values
    if force_flat:
        slope2 = 0
        intercept2 = np.polyfit(x2, y2, 0)
    else:
        slope2, intercept2 = np.polyfit(x2, y2, 1)

    x3 = neg_sat_section["field"].values
    y3 = neg_sat_section["magnetization"].values
    if force_flat:
        slope3 = 0
        intercept3 = np.polyfit(x3, y3, 0)
    else:
        slope3, intercept3 = np.polyfit(x3, y3, 1)

    positive_intercept_field = (intercept2 - intercept1) / (slope1 - slope2)
    negative_intercept_field = (intercept3 - intercept1) / (slope1 - slope3)

    # Make dictionary with results from the fits, can be used for plotting
    fit_dict = {
        "linear_section": [float(intercept1), float(slope1)],
        "positive_section": [float(intercept2), float(slope2)],
        "negative_section": [float(intercept3), float(slope3)],
    }

    return float(positive_intercept_field), float(negative_intercept_field), fit_dict


def moke_batch_fit(moke_group, treatment_dict):
    results_dict = {}
    for position, position_group in moke_group.items():
        if "scan_parameters" in position:
            continue

        mean_shot_group = position_group.get("measurement/shot_mean")

        magnetization_array = mean_shot_group["magnetization_mean"][()]
        pulse_array = mean_shot_group["pulse_mean"][()]
        reflectivity_array = mean_shot_group["reflectivity_mean"][()]
        integrated_pulse_array = mean_shot_group["integrated_pulse_mean"][()]
        
        measurement_dataframe = pd.DataFrame({"magnetization": magnetization_array, "pulse": pulse_array, "reflectivity": reflectivity_array,
                                              "integrated_pulse": integrated_pulse_array})

        measurement_dataframe = moke_treat_measurement_dataframe(measurement_dataframe, treatment_dict)

        max_kerr_rotation = moke_calc_max_kerr_rotation(measurement_dataframe)
        reflectivity = moke_calc_reflectivity(measurement_dataframe)
        coercivity_m0 = list(moke_calc_mzero_coercivity(measurement_dataframe))
        coercivity_dmdh = list(moke_calc_derivative_coercivity(measurement_dataframe))
        intercepts = list(moke_fit_intercept(measurement_dataframe, treatment_dict))

        results_dict[f"{position}"] = {
            "max_kerr_rotation":max_kerr_rotation,
            "reflectivity":reflectivity,
            "coercivity_m0":{"negative":coercivity_m0[0], "positive":coercivity_m0[1], "mean":abs_mean(coercivity_m0)},
            "coercivity_dmdh":{"negative":coercivity_dmdh[0], "positive":coercivity_dmdh[1], "mean":abs_mean(coercivity_dmdh)},
            "intercept_field":{"negative":intercepts[0], "positive":intercepts[1], "mean":abs_mean(intercepts[:2]), "coefficients":intercepts[2]},
        }
            
    return results_dict


def moke_results_dict_to_hdf5(moke_group, results_dict, treatment_dict=None):
    if treatment_dict is None:
        treatment_dict = {}

    for position in list(moke_group.keys()):
        if "scan_parameters" in position:
            continue
        position_group = moke_group[position]
        if position in results_dict.keys():

            if "results" in position_group:
                del position_group["results"]

            results_group = position_group.create_group("results")
            parameters_group = results_group.create_group("parameters")
            for key, value in treatment_dict.items():
                parameters_group.create_dataset(key, data=value)

            save_results_dict_to_hdf5(results_group, results_dict[position])

    return True


def moke_make_results_dataframe_from_hdf5(moke_group):
    data_dict_list = []

    for position, position_group in moke_group.items():
        if "scan_parameters" in position:
            continue
        instrument_group = position_group.get("instrument")
        # Exclude spots outside the wafer
        if np.abs(instrument_group["x_pos"][()]) + np.abs(instrument_group["y_pos"][()]) <= 60:

            results_group = position_group.get("results")

            data_dict = {"x_pos (mm)": instrument_group["x_pos"][()], "y_pos (mm)": instrument_group["y_pos"][()]}

            if results_group is None:
                continue

            for value, value_group in results_group.items():
                if "units" in value_group.attrs:
                    units = value.attrs["units"]
                else:
                    units = "arb"

                if value == "parameters":
                    continue
                elif isinstance(value_group, h5py.Group):
                    data_dict[f"{value}"] = value_group['mean'][()]
                elif isinstance(value_group, h5py.Dataset):
                    data_dict[f"{value}"] = value_group[()]

            data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def moke_plot_oscilloscope_from_dataframe(fig, df):
    pulse_shift_factor = df["pulse"].mean()
    magnetization_shift_factor = df["magnetization"].mean() - 0.5
    reflectivity_shift_factor = df["reflectivity"].mean() - 1

    fig.update_xaxes(title_text="Time (units)")
    fig.update_yaxes(title_text="Voltage (V)")

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["magnetization"].apply(lambda x: x - magnetization_shift_factor),
            mode="lines",
            line=dict(color="SlateBlue", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["reflectivity"].apply(lambda x: x - reflectivity_shift_factor),
            mode="lines",
            line=dict(color="Crimson", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["pulse"].apply(lambda x: x - pulse_shift_factor),
            mode="lines",
            line=dict(color="Green", width=2),
        )
    )
    return fig


def moke_plot_loop_from_dataframe(fig, df):
    fig.update_xaxes(title_text="Field (T)")
    fig.update_yaxes(title_text="Kerr rotation (deg)")

    fig.add_trace(
        go.Scatter(
            x=df["field"],
            y=df["magnetization"],
            mode="markers",
            line=dict(color="SlateBlue", width=3),
        )
    )
    return fig


def moke_plot_vlines(fig, values):
    for value in values:
        fig.add_vline(
            value,
            line_width=2,
            line_color="Firebrick",
            annotation_text=f"{value:.2f} T",
            annotation_font_size=14,
            annotation_font_color="Firebrick",
        )

    return fig


def moke_plot_loop_map(hdf5_file, options_dict, normalize = False):
    results_dataframe = moke_make_results_dataframe_from_hdf5(hdf5_file)
    instrument_dict = moke_get_instrument_dict_from_hdf5(hdf5_file)

    x_min, x_max = results_dataframe["x_pos (mm)"].min(), results_dataframe["x_pos (mm)"].max()
    y_min, y_max = results_dataframe["y_pos (mm)"].min(), results_dataframe["y_pos (mm)"].max()

    x_dim, y_dim = int(instrument_dict["number_of_points_x"]), int(instrument_dict["number_of_points_y"])

    if x_dim == 1:
        step_x = 1
    else:
        step_x = (np.abs(x_max) + np.abs(x_min)) / (x_dim - 1)

    if y_dim == 1:
        step_y = 1
    else:
        step_y = (np.abs(y_max) + np.abs(y_min)) / (y_dim - 1)

    fig = make_subplots(
        rows=y_dim, cols=x_dim, horizontal_spacing=0.001, vertical_spacing=0.001
    )

    # Update layout to hide axis lines, grid, and ticks for each subplot
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)

    # Update layout for aesthetics
    fig.update_layout(
        height=1000,
        width=1200,
        title_text="",
        showlegend=False,
        plot_bgcolor="white",
    )

    for index, row in results_dataframe.iterrows():
        target_x = row["x_pos (mm)"]
        target_y = row["y_pos (mm)"]

        data = moke_get_measurement_from_hdf5(hdf5_file, target_x, target_y)
        data = moke_treat_measurement_dataframe(data, options_dict)
        print(data)

        fig_col = int((target_x // step_x + (x_dim + 1) // 2))
        fig_row = int((-target_y // step_y + (y_dim + 1) // 2))

        fig.add_trace(
            go.Scatter(
                x=data["field"],
                y=data["magnetization"],
                mode="markers",
                line=dict(color="SlateBlue", width=1),
            ),
            row=fig_row,
            col=fig_col,
        )

        if normalize:
            fig.update_yaxes(
                range=[data["magnetization"].min(), data["magnetization"].max()],
                row=fig_row,
                col=fig_col,
            )
        if not normalize:
            y_max = results_dataframe["max_kerr_rotation"].max()
            fig.update_yaxes(range=[-y_max, y_max], row=fig_row, col=fig_col)

    return fig





















