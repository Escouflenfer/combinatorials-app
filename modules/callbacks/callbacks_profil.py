import sys, os

from dash import Input, Output, State, ctx
import subprocess
import plotly.graph_objects as go

from dash.exceptions import PreventUpdate
from ..functions.functions_profil import *

"""Callbacks for profil tab"""


def callbacks_profil(app):

    # Callback to update current position based on heatmap click
    @app.callback(
        Output("profil_position_store", "data"),
        Input("profil_heatmap", "clickData"),
        prevent_initial_call=True,
    )
    def profil_update_position(clickData):
        if clickData is None:
            return None
        target_x = clickData["points"][0]["x"]
        target_y = clickData["points"][0]["y"]

        position = (target_x, target_y)

        return position


    # Callback to check if HDF5 has results
    @app.callback(
        Output("profil_text_box", "children", allow_duplicate=True),
        Input("hdf5_path_store", "data"),
        prevent_initial_call=True,
    )
    def profil_check_for_results(hdf5_path):
        if check_hdf5_for_results(hdf5_path, 'profil', mode='all'):
            return 'Found results for all points'
        elif check_hdf5_for_results(hdf5_path, 'profil', mode='any'):
            return 'Found results for some points'
        else:
            return'No results found'


    # Callback for heatmap plot selection
    @app.callback(
        [
            Output("profil_heatmap", "figure", allow_duplicate=True),
            Output("profil_heatmap_min", "value"),
            Output("profil_heatmap_max", "value"),
        ],
        Input("profil_heatmap_select", "value"),
        Input("profil_heatmap_min", "value"),
        Input("profil_heatmap_max", "value"),
        Input("profil_heatmap_precision", "value"),
        Input("profil_heatmap_edit", "value"),
        Input('hdf5_path_store', 'data'),
        prevent_initial_call=True,
    )
    def profil_update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path):
        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate

        if ctx.triggered_id in ["profil_heatmap_select", "profil_heatmap_edit", "profil_heatmap_precision"]:
            z_min = None
            z_max = None

        masking = True
        if edit_toggle in ["edit", "unfiltered"]:
            masking = False

        profil_df = profil_make_results_dataframe_from_hdf5(hdf5_path)
        fig = make_heatmap_from_dataframe(profil_df, values=heatmap_select, z_min=z_min, z_max=z_max, precision=precision)

        z_min = np.round(fig.data[0].zmin, precision)
        z_max = np.round(fig.data[0].zmax, precision)

        return fig, z_min, z_max

    # Profile plot
    @app.callback(
        Output("profil_plot", "figure"),
        Input("hdf5_path_store", "data"),
        Input("profil_position_store", "data"),
        Input("profil_plot_select", "value")
    )
    def profil_update_plot(hdf5_path, position, plot_options):
        if hdf5_path is None:
            raise PreventUpdate
        if position is None:
            raise PreventUpdate

        hdf5_path = Path(hdf5_path)

        target_x = position[0]
        target_y = position[1]

        measurement_df = profil_get_measurement_from_hdf5(hdf5_path, target_x, target_y)
        results_dict = profil_get_results_from_hdf5(hdf5_path, target_x, target_y)

        options_dict = {}
        if 'Adjusting Slope' in plot_options:
            options_dict['Adjusting Slope'] = results_dict['Adjusting Slope']
        if 'Profile Fits' in plot_options:
            options_dict['Top fit coefficients'] = results_dict['Top fit coefficients']
            options_dict['Bottom fit coefficients'] = results_dict['Bottom fit coefficients']

        fig = profil_plot_measurement_from_dataframe(measurement_df, options_dict)

        return fig


    # Refitting results
    @app.callback(
        [Output("profil_text_box", "children", allow_duplicate=True),
         Output("hdf5_path_store", "data", allow_duplicate=True)],
        Input("profil_fit_button", "n_clicks"),
        State("profil_fit_height", "value"),
        State("profil_fit_degree", "value"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True,
    )

    def profil_refit_data(n_clicks, fit_height, fit_degree, hdf5_path):
        if hdf5_path is None:
            raise PreventUpdate
        parameters_dict={
            "Estimated height": fit_height,
            "Degree": fit_degree,
        }
        if n_clicks > 0:
            check = profil_batch_fit_poly(hdf5_path, parameters_dict)
            if check:
                return 'Successfully refitted data', hdf5_path

    # # Callback to deal with heatmap edit mode
    # @app.callback(
    #     Output("profil_text_box", "children", allow_duplicate=True),
    #     Input("profil_heatmap", "clickData"),
    #     State("profil_heatmap_edit", "value"),
    #     State("profil_database_path_store", "data"),
    #     State("profil_database_metadata_store", "data"),
    #     prevent_initial_call=True,
    # )
    # def heatmap_edit_mode(clickData, edit_toggle, database_path, metadata):
    #     database_path = Path(database_path)
    #
    #     if edit_toggle != "edit":
    #         raise PreventUpdate
    #
    #     target_x = clickData["points"][0]["x"]
    #     target_y = clickData["points"][0]["y"]
    #
    #     database = pd.read_csv(database_path, comment="#")
    #
    #     test = (database["x_pos (mm)"] == target_x) & (
    #         database["y_pos (mm)"] == target_y
    #     )
    #     row_number = database[test].index[0]
    #
    #     try:
    #         if database.loc[row_number, "Ignore"] == 0:
    #             database.loc[row_number, "Ignore"] = 1
    #             save_with_metadata(database, database_path, metadata)
    #             return f"Point x = {target_x}, y = {target_y} set to ignore"
    #         else:
    #             database.loc[row_number, "Ignore"] = 0
    #             save_with_metadata(database, database_path, metadata)
    #             return f"Point x = {target_x}, y = {target_y} no longer ignored"
    #     except KeyError:
    #         return "Invalid database. Please delete and reload to make a new one"
