from scipy.signal import savgol_filter
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from sklearn.linear_model import RANSACRegressor, LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from functions_shared import *

def check_for_profil(hdf5_path):
    with h5py.File(hdf5_path, "r") as f:
        if 'profil' in f['entry'].keys():
            return True
        else:
            return False


def profil_get_measurement_from_hdf5(hdf5_path, target_x, target_y):
    if not check_for_profil(hdf5_path):
        raise KeyError("Profilometry not found in file. Please check your file")

    with h5py.File(hdf5_path, "r") as f:
        profil_group = f['entry/profil']
        for position, position_group in profil_group.items():
            instrument_group = position_group.get('instrument')
            if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
                measurement_group = position_group.get('measurement')

                distance_array = measurement_group['Distance'][()]
                profile_array = measurement_group['Profile'][()]

                measurement_dataframe = pd.DataFrame({"Distance (um)": distance_array, "Total Profile (nm)": profile_array})

                return measurement_dataframe


def profil_get_results_from_hdf5(hdf5_path, target_x, target_y):
    if not check_for_profil(hdf5_path):
        raise KeyError("Profilometry not found in file. Please check your file")

    data_dict = {}

    with h5py.File(hdf5_path, "r") as f:
        profil_group = f['entry/profil']
        for position, position_group in profil_group.items():
            instrument_group = position_group.get('instrument')
            if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
                try:
                    results_group = position_group.get('result')
                except KeyError:
                    raise KeyError('Results group not found in file')
                for value, value_group in results_group.items():
                    data_dict[value] = value_group[()]

    return data_dict


def profil_measurement_dataframe_treat(df, smoothing=True):
    # Calculate and remove linear component from profile with step point linear fit
    step = 100
    slope = (np.mean(df.iloc[-step:-1, 1].tolist()) - np.mean(df.iloc[0:step, 1].tolist())) / df.iat[-1, 0]
    df['Adjusted Profile (nm)'] = df['Total Profile (nm)'] - df['Distance (um)'] * slope - df.iat[0, 1]
    if smoothing:
        df['Adjusted Profile (nm)'] = savgol_filter(df['Adjusted Profile (nm)'], 100, 0)
    return slope, df


def profil_measurement_dataframe_fit_poly(df, est_height, degree = 3):
    results_dict = {}

    if 'Adjusted Profile (nm)' not in df.columns:
        slope, df = profil_measurement_dataframe_treat(df)
        results_dict['Adjusting Slope'] = slope

    distance_array = df['Distance (um)'].to_numpy()
    profil_array = df['Adjusted Profile (nm)'].to_numpy()

    # Split the data horizontally in two
    top_mask = profil_array > est_height / 2
    x_top = distance_array[top_mask].reshape(-1, 1)
    y_top = profil_array[top_mask]

    bottom_mask = profil_array <= est_height / 2
    x_bottom = distance_array[bottom_mask].reshape(-1, 1)
    y_bottom = profil_array[bottom_mask]

    poly = PolynomialFeatures(degree=degree, include_bias=False)
    x_poly_top = poly.fit_transform(x_top.reshape(-1, 1))
    x_poly_bottom = poly.fit_transform(x_bottom.reshape(-1, 1))

    # Fit for the top line
    ransac_top = RANSACRegressor(LinearRegression(), residual_threshold=None)
    ransac_top.fit(x_poly_top, y_top)
    top_coefficients = np.append(np.array(ransac_top.estimator_.intercept_), ransac_top.estimator_.coef_)

    # Fit for the bottom line
    ransac_bottom = RANSACRegressor(LinearRegression(), residual_threshold=None)
    ransac_bottom.fit(x_poly_bottom, y_bottom)
    bottom_coefficients = np.append(np.array(ransac_bottom.estimator_.intercept_), ransac_bottom.estimator_.coef_)

    results_dict['Top fit coefficients'] = top_coefficients
    results_dict['Bottom fit coefficients'] = bottom_coefficients

    difference_coefficients = top_coefficients - bottom_coefficients
    measured_height = np.mean(calc_poly(difference_coefficients, distance_array[-1]))

    results_dict['Measured Height'] = measured_height

    return results_dict


def profil_batch_fit(hdf5_path, parameters_dict):
    if not check_for_profil(hdf5_path):
        raise KeyError("Profilometry not found in file. Please check your file")

    try:
        est_height = parameters_dict['Estimated height']
    except KeyError:
        raise KeyError('Estimated height must be provided in parameter dictionary')

    try:
        degree = parameters_dict['Degree']
    except KeyError:
        degree = 3

    with h5py.File(hdf5_path, mode='a') as hdf5_file:
        profil_group = hdf5_file['entry/profil']
        for position, position_group in profil_group.items():
            measurement_group = position_group.get('measurement')

            distance_array = measurement_group['Distance'][()]
            profile_array = measurement_group['Profile'][()]

            measurement_dataframe = pd.DataFrame({"Distance (um)": distance_array, "Total Profile (nm)": profile_array})

            results_dict = profil_measurement_dataframe_fit_poly(measurement_dataframe, est_height, degree)

            if "results" in position_group:
                del position_group["results"]

            results = position_group.create_group("results")
            try:
                for key, result in results_dict.items():
                    results[key] = result
                results["Measured Height"].attrs["units"] = "nm"
            except KeyError:
                raise KeyError('Given results dictionary not compatible with current version of this function.'
                               'Check compatibility with fit function')

    return None


def profil_make_results_dataframe_from_hdf5(hdf5_path):
    if not check_for_profil(hdf5_path):
        raise KeyError("Profilometry not found in file. Please check your file")

    data_dict_list = []

    with h5py.File(hdf5_path, mode='r') as hdf5_file:
        profil_group = hdf5_file['entry/profil']

        for position, position_group in profil_group.items():
            instrument_group = position_group.get('instrument')
            # Exclude spots outside the wafer
            if np.abs(instrument_group["x_pos"][()]) + np.abs(instrument_group["y_pos"][()]) <= 60:

                results_group = position_group.get('results')

                data_dict = {"x_pos (mm)": instrument_group["x_pos"][()], "y_pos (mm)": instrument_group["y_pos"][()]}

                if results_group is None:
                    continue

                for value, value_group in results_group.items():
                    if value == 'Measured Height':
                        data_dict['Measured Height (nm)'] = value_group[()]
                data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def profil_plot_measurement_from_dataframe(df, results_dict={}):
    slope, df = profil_measurement_dataframe_treat(df)
    # Plot the data
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.6, 0.4],
        subplot_titles=("Fitted data", "Measured thicknesses"),
        shared_xaxes=True,
        vertical_spacing=0.1
    )


    # First plot for raw measurement and linear component
    fig.update_xaxes(title_text='Distance (um)', row=1, col=1)
    fig.update_yaxes(title_text='Profile (nm)', row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=df['Distance (um)'],
            y=df['Total Profile (nm)'],
            mode='lines',
            line=dict(color="SlateBlue", width=2),
        ), row = 1, col = 1
    )

    if 'Adjusting Slope' in results_dict.keys():
        fig.add_trace(
            go.Scatter(
                x=df['Distance (um)'],
                y=df['Distance (um)'] * results_dict['Adjusting Slope'] + df.iat[0,1],
                mode='lines',
                line=dict(color="Crimson", width=2),
            ), row = 1, col = 1
        )

    # Second plot for adjusted profile and fits
    fig.update_xaxes(title_text='Distance (um)', row=2, col=1)
    fig.update_yaxes(title_text='Thickness (nm)', row=2, col=1)

    fig.add_trace(
        go.Scatter(
            x=df['Distance (um)'],
            y=df['Adjusted profile (nm)'],
            mode='lines',
            line=dict(color="SlateBlue", width=2),
        ), row = 2, col = 1
    )

    if 'Top fit coefficients' in results_dict.keys():
        fig.add_trace(
            go.Scatter(
                x=df['Distance (um)'],
                y=calc_poly(results_dict['Top fit coefficients'], df['Distance (um)'].iloc[-1]),
                mode='lines',
                line=dict(color="Crimson", width=2),
            ), row = 2, col = 1
        )

    if 'Bottom fit coefficients' in results_dict.keys():
        fig.add_trace(
            go.Scatter(
                x=df['Distance (um)'],
                y=calc_poly(results_dict['Bottom fit coefficients'], df['Distance (um)'].iloc[-1]),
                mode='lines',
                line=dict(color="Crimson", width=2),
            ), row=2, col=1
        )


    fig.update_layout(plot_layout(''))

    return fig
