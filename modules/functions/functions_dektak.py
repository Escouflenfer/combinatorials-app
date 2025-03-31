import numpy as np
import pandas as pd
import re
from scipy.optimize import least_squares
from scipy.signal import savgol_filter
from scipy.stats import linregress
from natsort import natsorted
from IPython.display import clear_output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from pathlib import Path
from sklearn.linear_model import RANSACRegressor, LinearRegression

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

                distance_array = measurement_group['distance'][()]
                profile_array = measurement_group['profile'][()]

                measurement_dataframe = pd.DataFrame({"Distance (um)": distance_array, "Total Profile (nm)": profile_array})

                return measurement_dataframe


def profil_treat_measurement_dataframe(df, smoothing=True):
    # Calculate and remove linear component from profile with step point linear fit
    step = 100
    slope = (np.mean(df.iloc[-step:-1, 1].tolist()) - np.mean(df.iloc[0:step, 1].tolist())) / df.iat[-1, 0]
    df['Adjusted Profile (nm)'] = df['Total Profile (nm)'] - df['Distance (um)'] * slope - df.iat[0, 1]
    if smoothing:
        df['Adjusted Profile (nm)'] = savgol_filter(df['Adjusted Profile (nm)'], 100, 0)
    return slope, df


def profil_fit_lines_measurement_dataframe(df, est_height):
    results_dict = {}

    if 'Adjusted Profile (nm)' not in df.columns:
        slope, df = profil_treat_measurement_dataframe(df)
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

    # Fit for the top line
    ransac_top = RANSACRegressor(LinearRegression(), residual_threshold=None)
    ransac_top.fit(x_top, y_top)
    top_slope = ransac_top.estimator_.coef_[0]
    top_intercept = ransac_top.estimator_.intercept_
    
    # Fit for the bottom line
    ransac_bottom = RANSACRegressor(LinearRegression(), residual_threshold=None)
    ransac_bottom.fit(x_bottom, y_bottom)
    bottom_slope = ransac_bottom.estimator_.coef_[0]
    bottom_intercept = ransac_bottom.estimator_.intercept_

    results_dict['Top slope'] = top_slope
    results_dict['Top intercept'] = top_intercept
    results_dict['Bottom slope'] = bottom_slope
    results_dict['Bottom intercept'] = bottom_intercept

    return results_dict

