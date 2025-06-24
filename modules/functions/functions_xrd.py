"""
Functions used in XRD interactive plot using Dash.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: Pierre Le Berre - Institut Néel (pierre.le-berre@neel.cnrs.fr)
"""

import plotly.express as px
from itertools import cycle

from ..functions.functions_shared import *


def xrd_conditions(hdf5_path, *args, **kwargs):
    if hdf5_path is None:
        return False
    if not h5py.is_hdf5(hdf5_path):
        return False
    with h5py.File(hdf5_path, "r") as hdf5_file:
        dataset_list = get_hdf5_datasets(hdf5_file, dataset_type="xrd")
        if len(dataset_list) == 0:
            return False
    return True


def xrd_get_integrated_from_hdf5(xrd_group, target_x, target_y):
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    measurement_group = position_group.get("measurement")

    integrated_group = measurement_group.get("CdTe_integrate")

    q_array = integrated_group["q"][()]
    intensity_array = integrated_group["intensity"][0]

    measurement_dataframe = pd.DataFrame({"q": q_array, "intensity": intensity_array})

    return measurement_dataframe


def xrd_get_image_from_hdf5(xrd_group, target_x, target_y):
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    measurement_group = position_group.get("measurement")

    image_array = measurement_group["CdTe"][0]

    return image_array


def xrd_get_fits_from_hdf5(xrd_group, target_x, target_y):
    fits_dict = {}
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    fits_group = position_group.get("results/fits")
    for dataset, dataset_group in fits_group.items():
        fits_dict[dataset] = dataset_group[()]

    fits_dataframe = pd.DataFrame(fits_dict)
    return fits_dataframe


def xrd_get_results_from_hdf5(xrd_group, target_x, target_y):
    position_group = get_target_position_group(xrd_group, target_x, target_y)
    results_group = position_group.get("results")
    if results_group is None:
        raise KeyError("results group not found in file")
    data_dict = hdf5_group_to_dict(results_group)
    return data_dict


def xrd_make_results_dataframe_from_hdf5(xrd_group):
    OPTIONS_LIST = ["A", "C", "phase_fraction", "Rwp"]

    data_dict_list = []

    for position, position_group in xrd_group.items():
        if position == "alignment_scans":
            continue
        instrument_group = position_group.get("instrument")
        # Exclude spots outside the wafer
        if (
            np.abs(instrument_group["x_pos"][()])
            + np.abs(instrument_group["y_pos"][()])
            <= 60
        ):

            data_dict = {
                "x_pos (mm)": instrument_group["x_pos"][()],
                "y_pos (mm)": instrument_group["y_pos"][()],
                "ignored": position_group.attrs["ignored"],
            }

            # Check in phases for refined lattice parameters and weight fraction
            phases_group = position_group.get("results/phases")
            if phases_group is not None:
                for phase, phase_group in phases_group.items():
                    for value, value_group in phase_group.items():
                        if value in OPTIONS_LIST:
                            dataset = str(value_group[()].decode())
                            if "units" in value_group.attrs:
                                units = value_group.attrs["units"]
                            else:
                                units = "arb"

                            # Check if refined parameter is not UNDEF
                            value_str = dataset.split("+")[0]
                            if value_str == "UNDEF":
                                dataset = np.nan
                            else:
                                dataset = float(value_str)

                            data_dict[f"[{phase}]_{value}_({units})"] = dataset

            data_dict_list.append(data_dict)

            # Check in R_coefficients for Rwp
            phases_group = position_group.get("results/r_coefficients")
            if phases_group is not None:
                for value, r_group in phases_group.items():
                    if value == "Rwp":
                        rwp = float(str(r_group[()]).split("%")[0].replace("b'", ""))
                        dataset = rwp
                        if "units" in r_group.attrs:
                            units = r_group.attrs["units"]
                        else:
                            units = "%"
                        data_dict[f"{value}_({units})"] = dataset

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def xrd_plot_integrated_from_dataframe(fig, df):
    fig.update_xaxes(title_text="q (A-1)")
    fig.update_yaxes(title_text="Counts")

    fig.add_trace(
        go.Scatter(
            x=df["q"],
            y=df["intensity"],
            mode="lines",
            line=dict(color="SlateBlue", width=2),
        )
    )

    return fig


def xrd_plot_fits_from_dataframe(fig, df, fits=None):
    colors = cycle(px.colors.qualitative.Plotly)

    if not fits:
        fits = df.columns[1:]
    fig.update_xaxes(title_text="2th (°)")
    fig.update_yaxes(title_text="Counts")

    for fit in fits:
        fig.add_trace(
            go.Scatter(
                x=df["Angle"],
                y=df[fit],
                mode="lines",
                line=dict(color=next(colors), width=2),
                name=fit,
            )
        )
    return fig


def xrd_plot_image_from_array(array, z_min, z_max):
    if z_min is None:
        z_min = np.nanmin(array)
    if z_max is None:

        z_max = np.nanmax(array)

    fig = go.Figure(
        data=go.Heatmap(
            z=array,
            colorscale="Plasma",
            colorbar=colorbar_layout(z_min, z_max, precision=0, title="count"),
        )
    )

    fig.update_layout(
        title="Image",
        xaxis_title="x",
        yaxis_title="y",
        height=800,
        width=800,
        margin=dict(r=100, t=100),
    )

    if z_min is not None:
        fig.data[0].update(zmin=z_min)
    if z_max is not None:
        fig.data[0].update(zmax=z_max)

    return fig
