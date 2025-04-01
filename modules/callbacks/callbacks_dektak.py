import sys, os

from dash import Input, Output, State, ctx
import subprocess
import plotly.graph_objects as go

from dash.exceptions import PreventUpdate
from ..functions.functions_dektak import *

"""Callbacks for DEKTAK tab"""


def callbacks_dektak(app):

    # Callback to update current position based on heatmap click
    @app.callback(
        Output("dektak_position_store", "data"),
        Input("dektak_heatmap", "clickData"),
        prevent_initial_call=True,
    )
    def update_position(clickData):
        if clickData is None:
            return None
        target_x = clickData["points"][0]["x"]
        target_y = clickData["points"][0]["y"]

        position = (target_x, target_y)

        return position


    # Callback for heatmap plot selection
    @app.callback(
        [
            Output("dektak_heatmap", "figure", allow_duplicate=True),
            Output("dektak_heatmap_min", "value"),
            Output("dektak_heatmap_max", "value"),
        ],
        Input("dektak_heatmap_select", "value"),
        Input("dektak_heatmap_min", "value"),
        Input("dektak_heatmap_max", "value"),
        Input("dektak_heatmap_precision", "value"),
        Input("dektak_heatmap_edit", "value"),
        State('hdf5_path_store', 'data'),
        prevent_initial_call=True,
    )
    def update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path):
        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate

        if ctx.triggered_id in ["dektak_heatmap_select", "dektak_heatmap_edit", "dektak_heatmap_precision"]:
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
        Output("dektak_plot", "figure"),
        Input("hdf5_path_store", "data"),
        Input("dektak_position_store", "data"),
    )
    def edx_update_plot(hdf5_path, position):
        if hdf5_path is None:
            raise PreventUpdate
        if position is None:
            raise PreventUpdate

        hdf5_path = Path(hdf5_path)

        target_x = position[0]
        target_y = position[1]

        measurement_df = profil_get_measurement_from_hdf5(hdf5_path, target_x, target_y)
        fig = profil_plot_measurement_from_dataframe(measurement_df)

        return fig


    # Callback to deal with heatmap edit mode
    @app.callback(
        Output("dektak_text_box", "children", allow_duplicate=True),
        Input("dektak_heatmap", "clickData"),
        State("dektak_heatmap_edit", "value"),
        State("dektak_database_path_store", "data"),
        State("dektak_database_metadata_store", "data"),
        prevent_initial_call=True,
    )
    def heatmap_edit_mode(clickData, edit_toggle, database_path, metadata):
        database_path = Path(database_path)

        if edit_toggle != "edit":
            raise PreventUpdate

        target_x = clickData["points"][0]["x"]
        target_y = clickData["points"][0]["y"]

        database = pd.read_csv(database_path, comment="#")

        test = (database["x_pos (mm)"] == target_x) & (
            database["y_pos (mm)"] == target_y
        )
        row_number = database[test].index[0]

        try:
            if database.loc[row_number, "Ignore"] == 0:
                database.loc[row_number, "Ignore"] = 1
                save_with_metadata(database, database_path, metadata)
                return f"Point x = {target_x}, y = {target_y} set to ignore"
            else:
                database.loc[row_number, "Ignore"] = 0
                save_with_metadata(database, database_path, metadata)
                return f"Point x = {target_x}, y = {target_y} no longer ignored"
        except KeyError:
            return "Invalid database. Please delete and reload to make a new one"
