"""
callback functions used in XRD interface.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

from dash import Input, Output, callback
from dash.exceptions import PreventUpdate
from ..functions.functions_xrd import *
from ..functions.functions_shared import *


def callbacks_xrd(app, children_xrd):
    # XRD components
    @callback(
        Output("xrd_heatmap_select", "options", allow_duplicate=False),
        Output("xrd_heatmap_select", "value", allow_duplicate=False),
        Input("xrd_path_store", "data"),
        prevent_initial_call=True,
    )
    def update_data_type_options(foldername):
        refinement_options = check_xrd_refinement(foldername)

        if refinement_options is not False:
            display_options = [
                option for option in refinement_options if not option.endswith("_err")
            ]
            return (["Raw XRD data"] + display_options), "Raw XRD data"
        else:
            return ["Raw XRD data"], "Raw XRD data"

    # XRD heatmap
    @callback(
        Output("xrd_heatmap", "figure"),
        Output("xrd_heatmap_min", "value"),
        Output("xrd_heatmap_max", "value"),
        Input("xrd_path_store", "data"),
        Input("xrd_heatmap_select", "value"),
        Input("xrd_heatmap_min", "value"),
        Input("xrd_heatmap_max", "value"),
    )
    def update_xrd_heatmap(foldername, datatype, z_min, z_max):
        fig = plot_xrd_heatmap(foldername, datatype, z_min, z_max)

        if datatype == "Raw XRD data":
            title = "None"
        elif datatype.startswith("Q"):
            title = "Wgt. frac. (%)"
        else:
            title = "Lattice (Å)"

        z_min = significant_round(fig.data[0].zmin, 5)
        z_max = significant_round(fig.data[0].zmax, 5)

        return fig, z_min, z_max

    @callback(
        Output("xrd_heatmap_min", "value", allow_duplicate=True),
        Output("xrd_heatmap_max", "value", allow_duplicate=True),
        Input("xrd_heatmap_select", "value"),
        prevent_initial_call=True,
    )
    def update_z_values(datatype):
        return None, None

    # XRD single pattern
    @callback(
        Output("xrd_plot", "figure"),
        Input("xrd_path_store", "data"),
        Input("xrd_heatmap_select", "value"),
        Input("xrd_heatmap_select", "options"),
        Input("xrd_heatmap", "clickData"),
    )
    def update_xrd_pattern(foldername, datatype, options, clickData):
        foldername = pathlib.Path(foldername)

        # Check for both Smartlab and ESRF data
        measurement_list = create_coordinate_map(foldername)
        if measurement_list == []:
            measurement_list = create_coordinate_map(
                foldername, prefix=foldername.name, suffix=".xy"
            )

        if clickData is None:
            x_pos, y_pos = 0, 0
        else:
            x_pos = int(clickData["points"][0]["x"])
            y_pos = int(clickData["points"][0]["y"])

        for measurement in measurement_list:
            if x_pos == measurement[0] and y_pos == measurement[1]:
                xrd_filename = measurement[2]

        fig = plot_xrd_pattern(foldername, datatype, options, xrd_filename)

        fig.update_layout(
            height=650,
            width=1000,
            title=f"XRD spectra for {foldername} at position ({x_pos}, {y_pos})",
        )
        fig.update_xaxes(title="2Theta (°)")
        fig.update_yaxes(title="Counts")

        return fig
