"""
callback functions used in XRD interface.
Internal use for Institut Néel and within the MaMMoS project, to export and read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

from dash import Input, Output, callback
from ..functions.functions_xrd import *
from ..functions.functions_shared import *


def callbacks_xrd(app, children_xrd):
    # XRD components
    @callback(
        Output("xrd_heatmap_select", "options"),
        Output("xrd_heatmap_select", "value"),
        Input("xrd_path_store", "data"),
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
        fig, z_min_plot, z_max_plot = plot_xrd_heatmap(foldername, datatype)
        if z_min is None or z_max is None:
            z_min = z_min_plot
            z_max = z_max_plot

        # Update the dimensions of the heatmap and the X-Y title axes
        fig.update_layout(height=600, width=600, clickmode="event+select")
        fig.update_xaxes(title="X Position")
        fig.update_yaxes(title="Y Position")

        if datatype == "Raw XRD data":
            title = "None"
        elif datatype.startswith("Q"):
            title = "Wgt. frac. (%)"
        else:
            title = "Lattice (Å)"

        fig.data[0].update(zmin=z_min, zmax=z_max)

        if z_min is not None and z_max is not None:
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
        Input("xrd_tth_range_slider", "value"),
        Input("xrd_count_slider", "value"),
    )
    def update_xrd_pattern(foldername, datatype, options, clickData, xrange, yrange):
        if clickData is None:
            x_pos, y_pos = 0, 0
            xrd_filename = "Areamap_009009.ras"
        else:
            x_pos = int(clickData["points"][0]["x"])
            y_pos = int(clickData["points"][0]["y"])
            xrd_filename = clickData["points"][0]["text"]

        # print(foldername, x_pos, y_pos)
        fig = plot_xrd_pattern(
            foldername, datatype, options, xrd_filename, x_pos, y_pos
        )

        fig.update_layout(
            height=650,
            width=1000,
            title=f"XRD spectra for {foldername} at position ({x_pos}, {y_pos})",
        )
        fig.update_xaxes(title="2Theta (°)", range=xrange)
        fig.update_yaxes(title="Counts", range=yrange)

        return fig
