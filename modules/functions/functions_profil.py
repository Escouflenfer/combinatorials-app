from scipy.optimize import least_squares
from scipy.signal import savgol_filter
import plotly.graph_objs as go
from sklearn.linear_model import RANSACRegressor, LinearRegression
from functions_shared import *

def check_for_profil(hdf5_path):
    with h5py.File(hdf5_path, "r") as f:
        if "profil" in f.keys():
            return True
        else:
            return False


def profil_get_measurement_from_hdf5(profil_group, target_x, target_y):
    for position, position_group in profil_group.items():
        instrument_group = position_group.get("instrument")
        if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
            measurement_group = position_group.get("measurement")

            distance_array = measurement_group["distance"][()]
            profile_array = measurement_group["profile"][()]

            measurement_dataframe = pd.DataFrame({"distance_(um)": distance_array, "total_profile_(nm)": profile_array})

            return measurement_dataframe


def profil_get_results_from_hdf5(profil_group, target_x, target_y):
    data_dict = {}

    for position, position_group in profil_group.items():
        instrument_group = position_group.get("instrument")
        if instrument_group["x_pos"][()] == target_x and instrument_group["y_pos"][()] == target_y:
            results_group = position_group.get("results")
            if results_group is None:
                raise KeyError("results group not found in file")
            for value, value_group in results_group.items():
                data_dict[value] = value_group[()]

    return data_dict


def multi_step_function(x, *params):
    # Generate function with multiple steps
    # Even indices are the x positions of the steps,
    # Odd indices are the y values after each step.

    y = np.full_like(x, params[1])
    for i in range(0, len(params) - 2, 2):
        x0 = params[i]
        y1 = params[i + 3]
        y = np.where(x >= x0, y1, y)
    return y


def generate_parameters(height, x0, n_steps):
    guess = []
    length = 4000 / (2*n_steps) # Length of a step
    for n in range(n_steps+1):
        guess.append(x0+2*length*n) # Step up position
        guess.append(height) # Step up height
        guess.append(x0+length+2*length*n) # Step down position
        guess.append(0) # Step down height
    return guess


def extract_fit(fitted_params):
    # Separate fitted parameters
    fit_position_list = []
    fit_height_list = []
    for position, height in pairwise(fitted_params):
        fit_position_list.append(np.round(position, 1))
        fit_height_list.append(np.round(height, 1))

    # From fitted parameters, calculate positions
    position_list = []
    for n in range(len(fit_position_list) - 1):
        a = fit_position_list[n]
        b = fit_position_list[n + 1]
        position_list.append(np.round(np.abs(b - (b - a) / 2), 1))
    position_list.pop()

    # From fitted parameters, calculate heights
    height_list = []
    for n in range(len(fit_height_list) - 1):
        a = fit_height_list[n]
        b = fit_height_list[n + 1]
        height_list.append(np.round(np.abs(a - b), 1))
    height_list.pop()

    return position_list, height_list


def residuals(params, x, y):
    # Loss function for fitting
    return y - multi_step_function(x, *params)


def profil_measurement_dataframe_treat(df, slope=None, smoothing=True):
    # Calculate and remove linear component from profile with step point linear fit
    if slope is None:
        step = 100
        slope = (np.mean(df.iloc[-step:-1, 1].tolist()) - np.mean(df.iloc[0:step, 1].tolist())) / df.iat[-1, 0]

    df["adjusted_profile_(nm)"] = df["total_profile_(nm)"] - df["distance_(um)"] * slope - df.iat[0, 1]
    if smoothing:
        df["adjusted_profile_(nm)"] = savgol_filter(df["adjusted_profile_(nm)"], 100, 0)

    return slope, df


def profil_measurement_dataframe_fit_steps(df, est_height, n_steps):
    results_dict = {}

    if "adjusted_profile_(nm)" not in df.columns:
        slope, df = profil_measurement_dataframe_treat(df, smoothing=True)
        results_dict["adjusting_slope"] = slope

    # Detect the position of the first step of the measurement
    df = derivate_dataframe(df, "total_profile_(nm)")
    df_head = df.loc[df["distance_(um)"] < 600]
    max_index = df_head["derivative"].idxmax()
    x0 = df_head.loc[max_index, "distance_(um)"]

    distance_array = df["distance_(um)"].to_numpy()
    profile_array = df["adjusted_profile_(nm)"].to_numpy()

    guess = generate_parameters(height = est_height, x0 = x0, n_steps = n_steps)

    result = least_squares(residuals, guess, jac="2-point", args=(distance_array, profile_array), loss="soft_l1")
    fitted_params = result.x

    position_list, height_list = extract_fit(fitted_params)

    results_dict["fit_parameters"] = fitted_params
    results_dict["extracted_positions"] = position_list
    results_dict["extracted_heights"] = height_list
    results_dict["measured_height"] = np.mean(height_list).round()

    # ransac = RANSACRegressor(LinearRegression(), residual_threshold=None)
    # ransac.fit(position_list, height_list)
    # top_coefficients = np.append(np.array(ransac.estimator_.intercept_), ransac.estimator_.coef_)

    return results_dict


def profil_batch_fit_steps(profil_group, est_height, nb_steps):
    for position, position_group in profil_group.items():
        measurement_group = position_group.get("measurement")

        distance_array = measurement_group["distance"][()]
        profile_array = measurement_group["profile"][()]

        measurement_dataframe = pd.DataFrame({"distance_(um)": distance_array, "total_profile_(nm)": profile_array})

        results_dict = profil_measurement_dataframe_fit_steps(measurement_dataframe, est_height, nb_steps)

        if "results" in position_group:
            del position_group["results"]

        results = position_group.create_group("results")
        try:
            for key, result in results_dict.items():
                results[key] = result
            results["measured_height"].attrs["units"] = "nm"
        except KeyError:
            raise KeyError("Given results dictionary not compatible with current version of this function."
                           "Check compatibility with fit function")

    return True



def profil_make_results_dataframe_from_hdf5(profil_group):
    data_dict_list = []

    for position, position_group in profil_group.items():
        instrument_group = position_group.get("instrument")
        # Exclude spots outside the wafer
        if np.abs(instrument_group["x_pos"][()]) + np.abs(instrument_group["y_pos"][()]) <= 60:

            results_group = position_group.get("results")

            data_dict = {"x_pos (mm)": instrument_group["x_pos"][()], "y_pos (mm)": instrument_group["y_pos"][()]}

            if results_group is None:
                continue

            for value, value_group in results_group.items():
                if "units" in value.attrs:
                    units = value.attrs["units"]
                else:
                    units = "arb"
                data_dict[f"{value}_({units})"] = value_group[()]
            data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def profil_plot_total_profile_from_dataframe(fig, df, results_dict=None, position=(1,1)):
    # First plot for raw measurement and linear component
    if results_dict is None:
        results_dict = {}

    fig.update_xaxes(title_text="Distance_(um)", row=1, col=1)
    fig.update_yaxes(title_text="Profile_(nm)", row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=df["distance_(um)"],
            y=df["total_profile_(nm)"],
            mode="lines",
            line=dict(color="SlateBlue", width=3),
        ), row = position[0], col = position[1]
    )

    if "adjusting_slope" in results_dict.keys():
        fig.add_trace(
            go.Scatter(
                x=df["distance_(um)"],
                y=df["total_profile_(nm)"].iat[0] + df["distance_(um)"] * results_dict["adjusting_slope"],
                mode="lines",
                line=dict(color="Crimson", width=2),
            ), row = position[0], col = position[1]
        )

    return fig


def profil_plot_adjusted_profile_from_dataframe(fig, df, results_dict=None, position=(2,1)):
    if results_dict is None:
        results_dict = {}

    # Second plot for adjusted profile and fits
    fig.update_xaxes(title_text="Distance_(um)", row=2, col=1)
    fig.update_yaxes(title_text="Thickness_(nm)", row=2, col=1)

    fig.add_trace(
        go.Scatter(
            x=df["distance_(um)"],
            y=df["adjusted_profile_(nm)"],
            mode="lines",
            line=dict(color="SlateBlue", width=3),
        ), row=position[0], col=position[1]
    )

    if "fit_parameters" in results_dict.keys():
        fig.add_trace(
            go.Scatter(
                x=df["distance_(um)"],
                y=multi_step_function(df["distance_(um)"], *results_dict["fit_parameters"]),
                mode="lines",
                line=dict(color="Crimson", width=2),
            ), row=position[0], col=position[1]
        )

    return fig


def profil_plot_measured_heights_from_dict(fig, results_dict, position=(3,1)):
    position_list = results_dict["extracted_positions"]
    height_list = results_dict["extracted_heights"]
    measured_height = results_dict["measured_height"]

    # Third plot
    fig.update_xaxes(title_text="Distance_(um)", row=2, col=1)
    fig.update_yaxes(title_text="Thickness_(nm)", row=2, col=1)

    # Scattered heights
    fig.add_trace(
        go.Scatter(x=position_list, y=height_list,
                   mode="markers",
                   # name="Measured thickness",
                   line=dict(color="SlateBlue ", width=3)),
        row=position[0], col=position[1]
    )

    # Mean line
    fig.add_hline(y=measured_height, line=dict(color="Crimson", width=2), row=position[0], col=position[1])

    return fig




























"""
ARCHIVE FOR POLYNOMIAL FIT, MIGHT COME BACK TO IT SOMEDAY
"""

# def profil_measurement_dataframe_fit_poly(df, est_height, degree = 3):
#     results_dict = {}
#
#     if "adjusted_profile_(nm)" not in df.columns:
#         slope, df = profil_measurement_dataframe_treat(df, smoothing=True)
#         results_dict["adjusting_slope"] = slope
#
#     distance_array = df["distance_(um)"].to_numpy()
#     profile_array = df["adjusted_profile_(nm)"].to_numpy()
#
#     # Split the data horizontally in two
#     top_mask = profile_array > est_height / 2
#     x_top = distance_array[top_mask].reshape(-1, 1)
#     y_top = profile_array[top_mask]
#
#     bottom_mask = profile_array <= est_height / 2
#     x_bottom = distance_array[bottom_mask].reshape(-1, 1)
#     y_bottom = profile_array[bottom_mask]
#
#     poly = PolynomialFeatures(degree=degree, include_bias=False)
#     x_poly_top = poly.fit_transform(x_top.reshape(-1, 1))
#     x_poly_bottom = poly.fit_transform(x_bottom.reshape(-1, 1))
#
#     # Fit for the top line
#     ransac_top = RANSACRegressor(LinearRegression(), residual_threshold=None)
#     ransac_top.fit(x_poly_top, y_top)
#     top_coefficients = np.append(np.array(ransac_top.estimator_.intercept_), ransac_top.estimator_.coef_)
#
#     # Fit for the bottom line
#     ransac_bottom = RANSACRegressor(LinearRegression(), residual_threshold=None)
#     ransac_bottom.fit(x_poly_bottom, y_bottom)
#     bottom_coefficients = np.append(np.array(ransac_bottom.estimator_.intercept_), ransac_bottom.estimator_.coef_)
#
#     results_dict["Top fit coefficients"] = top_coefficients
#     results_dict["Bottom fit coefficients"] = bottom_coefficients
#
#     difference_coefficients = top_coefficients - bottom_coefficients
#     measured_height = np.mean(calc_poly(difference_coefficients, distance_array[-1]))
#
#     results_dict["measured_height"] = measured_height
#
#     return results_dict
#
#
# def profil_batch_fit_poly(hdf5_path, est_height, degree=3):
#     if not check_for_profil(hdf5_path):
#         raise KeyError("Profilometry not found in file. Please check your file")
#
#     with h5py.File(hdf5_path, mode="a") as hdf5_file:
#         profil_group = hdf5_file["/profil"]
#         for position, position_group in profil_group.items():
#             measurement_group = position_group.get("measurement")
#
#             distance_array = measurement_group["distance"][()]
#             profile_array = measurement_group["profile"][()]
#
#             measurement_dataframe = pd.DataFrame({"distance_(um)": distance_array, "total_profile_(nm)": profile_array})
#
#             results_dict = profil_measurement_dataframe_fit_poly(measurement_dataframe, est_height, degree)
#
#             if "results" in position_group:
#                 del position_group["results"]
#
#             results = position_group.create_group("results")
#             try:
#                 for key, result in results_dict.items():
#                     results[key] = result
#                 results["measured_height"].attrs["units"] = "nm"
#             except KeyError:
#                 raise KeyError("Given results dictionary not compatible with current version of this function."
#                                "Check compatibility with fit function")
#
#     return True

# def profil_plot_poly_measurement_from_dataframe(df, results_dict={}):
#     slope, df = profil_measurement_dataframe_treat(df)
#
#     # Plot the data
#     fig = make_subplots(
#         rows=2,
#         cols=1,
#         row_heights=[0.6, 0.4],
#         subplot_titles=("Fitted data", "Measured thicknesses"),
#         shared_xaxes=True,
#         vertical_spacing=0.1
#     )
#
#
#     # First plot for raw measurement and linear component
#     fig.update_xaxes(title_text="distance_(um)", row=1, col=1)
#     fig.update_yaxes(title_text="profile_(nm)", row=1, col=1)
#
#     fig.add_trace(
#         go.Scatter(
#             x=df["distance_(um)"],
#             y=df["total_profile_(nm)"],
#             mode="lines",
#             line=dict(color="SlateBlue", width=2),
#         ), row = 1, col = 1
#     )
#
#     if "adjusting_slope" in results_dict.keys():
#         fig.add_trace(
#             go.Scatter(
#                 x=df["distance_(um)"],
#                 y=df["distance_(um)"] * results_dict["adjusting_slope"] + df.iat[0,1],
#                 mode="lines",
#                 line=dict(color="Crimson", width=2),
#             ), row = 1, col = 1
#         )
#
#     # Second plot for adjusted profile and fits
#     fig.update_xaxes(title_text="distance_(um)", row=2, col=1)
#     fig.update_yaxes(title_text="Thickness_(nm)", row=2, col=1)
#
#     fig.add_trace(
#         go.Scatter(
#             x=df["distance_(um)"],
#             y=df["adjusted_profile_(nm)"],
#             mode="lines",
#             line=dict(color="SlateBlue", width=2),
#         ), row = 2, col = 1
#     )
#
#     if "Top fit coefficients" in results_dict.keys():
#         polynomial = calc_poly(results_dict["Top fit coefficients"], x_end=df["distance_(um)"].iloc[-1], x_start=0, x_step=df["distance_(um)"].iloc[-1]/len(df["distance_(um)"]))
#         fig.add_trace(
#             go.Scatter(
#                 x=df["distance_(um)"],
#                 y=polynomial,
#                 mode="lines",
#                 line=dict(color="Crimson", width=2),
#             ), row = 2, col = 1
#         )
#
#     if "Bottom fit coefficients" in results_dict.keys():
#         polynomial = calc_poly(results_dict["Bottom fit coefficients"], x_end=df["distance_(um)"].iloc[-1], x_start=0,
#                                x_step=df["distance_(um)"].iloc[-1] / len(df["distance_(um)"]))
#         fig.add_trace(
#             go.Scatter(
#                 x=df["distance_(um)"],
#                 y=polynomial,
#                 mode="lines",
#                 line=dict(color="Crimson", width=2),
#             ), row=2, col=1
#         )
#
#
#     fig.update_layout(plot_layout(""))
#
#     return fig



