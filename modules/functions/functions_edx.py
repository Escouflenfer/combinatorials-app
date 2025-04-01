"""
Functions used in EDX interactive plot using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

from ..functions.functions_shared import *


def check_for_edx(hdf5_path):
    with h5py.File(hdf5_path, "r") as f:
        if 'edx' in f['entry'].keys():
            return True
        else:
            return False


def get_quantified_elements(hdf5_path):
    if not check_for_edx(hdf5_path):
        raise KeyError("EDX not found in file. Please check your file")

    element_list = []

    with h5py.File(hdf5_path, "r") as f:
        edx_group = f['entry/edx']

        for position, position_group in edx_group.items():
            results_group = position_group.get('results')

            if results_group is None:
                continue

            for element, element_group in results_group.items():
                if 'AtomPercent' in element_group and element not in element_list:
                    element_list.append(element)
    return element_list


def edx_make_results_dataframe_from_hdf5(hdf5_path):
    if not check_for_edx(hdf5_path):
        raise KeyError("EDX not found in file. Please check your file")

    data_dict_list = []

    with h5py.File(hdf5_path, "r") as f:
        edx_group = f['entry/edx']

        for position, position_group in edx_group.items():
            instrument_group = position_group.get('instrument')
            # Exclude spots outside the wafer
            if np.abs(instrument_group["x_pos"][()]) + np.abs(instrument_group["y_pos"][()]) <= 60:

                results_group = position_group.get('results')

                data_dict = {"x_pos (mm)": instrument_group["x_pos"][()], "y_pos (mm)": instrument_group["y_pos"][()]}

                if results_group is None:
                    continue

                for element, element_group in results_group.items():
                    if 'AtomPercent' in element_group:
                        data_dict[element] = element_group['AtomPercent'][()]
                data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def edx_get_measurement_from_hdf5(hdf5_path, target_x, target_y):
    if not check_for_edx(hdf5_path):
        raise KeyError("EDX not found in file. Please check your file")

    with h5py.File(hdf5_path, "r") as f:
        edx_group = f['entry/edx']
        for position, position_group in edx_group.items():
            instrument_group = position_group.get('instrument')
            if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
                measurement_group = position_group.get('measurement')

                energy_array = measurement_group['energy'][()]
                counts_array = measurement_group['counts'][()]

                spectrum_dataframe = pd.DataFrame({"Energy (keV)": energy_array, "Counts": counts_array})

                return spectrum_dataframe


def edx_plot_measurement_from_dataframe(df):
    fig = go.Figure(layout = plot_layout(''))

    fig.add_trace(
        go.Scatter(
            x=df['Energy (keV)'],
            y=df['Counts'],
            mode='lines',
            line=dict(color="SlateBlue", width=2),
        )
    )

    return fig