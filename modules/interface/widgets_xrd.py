"""
class file for xrd widgets using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import os
from dash import html, dcc
from itertools import count, takewhile


def frange(start, stop, step):
    """
    frange(start, stop, step) -> generator

    Generate a sequence of numbers over a specified range.
    Like the built-in range() function, but returns a generator
    instead of a list. Used for floating-point ranges.

    Parameters
    ----------
        start (int or float): The first number in the sequence.
        stop (int or float): The sequence stops before this number.
        step (int or float): The difference between each number in the sequence.

    Returns
    ----------
        The next number in the sequence.
    """
    return takewhile(lambda x: x < stop, count(start, step))


class WidgetsXRD:

    def __init__(self, folderpath):
        """
        Initialization of the XRD widgets.

        Creates all the components needed for the XRD interactive tab:
        - Folderpath dropdown
        - Browse button
        - Slider Xrange
        - Slider Yrange
        - Colorange for heatmap
        - Dropdown for data type
        - XRD spectra graph
        - XRD heatmap
        """
        # Folderpath for the xrd pattern
        self.folderpath = folderpath

        # XRD Widget for the center box
        self.xrd_center = html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[html.Span(children="test", id="xrd_path_box")],
                ),
                html.Div(
                    className="text-mid",
                    children=[html.Span(children="test", id="xrd_text_box")],
                ),
            ],
        )

        # XRD Widget for the left box
        self.xrd_left = html.Div(
            className="subgrid top-left",
            children=[
                html.Div(
                    className="subgrid-2",
                    children=[
                        html.Label("Refined Parameter:"),
                        html.Br(),
                        dcc.Dropdown(
                            id="xrd_heatmap_select",
                            className="long-item",
                            options=["Raw XRD Data"],
                            value="Raw XRD Data",
                        ),
                    ],
                ),
                html.Div(
                    className="subgrid-7",
                    children=[
                        html.Label("Colorbar bounds"),
                        dcc.Input(
                            id="xrd_heatmap_max",
                            className="long-item",
                            type="number",
                            placeholder="maximum value",
                            value=None,
                        ),
                        dcc.Input(
                            id="xrd_heatmap_min",
                            className="long-item",
                            type="number",
                            placeholder="minimum value",
                            value=None,
                        ),
                    ],
                ),
                html.Div(
                    className="subgrid-9",
                    children=[
                        html.Label(""),
                        html.Br(),
                        dcc.RadioItems(
                            id="xrd_heatmap_edit",
                            options=[
                                {"label": "Unfiltered", "value": "unfiltered"},
                                {"label": "Filtered", "value": "filter"},
                                {"label": "Edit mode", "value": "edit"},
                            ],
                            value="filter",
                            style={"display": "inline-block"},
                        ),
                    ],
                ),
            ],
        )

        # XRD Widget for the right box (XRD spectra plotting)
        self.xrd_right = html.Div(
            className="subgrid top-right",
            children=[
                html.Div(
                    className="subgrid 2",
                    children=[
                        html.Label("2Theta (°)"),
                        dcc.RangeSlider(
                            min=0,
                            max=120,
                            step=1,
                            value=[20, 70],
                            marks={i: f"{i}" for i in range(0, 120 + 10, 10)},
                            id="xrd_tth_range_slider",
                            className="long-item",
                        ),
                    ],
                ),
                html.Div(
                    className="subgrid 7",
                    children=[
                        html.Label("Counts"),
                        dcc.RangeSlider(
                            min=-25000,
                            max=200000,
                            step=1000,
                            value=[-4000, 40000],
                            marks={i: f"{i}k" for i in frange(-25, 200 + 25, 25)},
                            id="xrd_count_slider",
                            className="long-item",
                        ),
                    ],
                ),
            ],
        )

        # XRD spectra graph that will be modified by user interaction
        self.xrd_pattern = html.Div(
            [
                dcc.Graph(id="xrd_plot"),
                html.Button("Save!", id="xrd_plot_save", n_clicks=0),
            ],
            className="plot-right",
        )

        # XRD heatmap
        self.xrd_heatmap = html.Div(
            [
                dcc.Graph(id="xrd_heatmap"),
                html.Button("Save!", id="xrd_heatmap_save", n_clicks=0),
            ],
            className="plot-left",
        )

        # Stored variables
        self.xrd_stores = html.Div(
            children=[
                dcc.Store(id="xrd_position_store", data=None),
                dcc.Store(id="xrd_database_path_store", data=None),
                dcc.Store(id="xrd_heatmap_replot_tag", data=False),
                dcc.Store(id="xrd_database_metadata_store", data=None),
            ]
        )

    # def get_children(self, className_moke="grid_layout_xrd"):
    #     """
    #     Return a Div containing all the components of the XRD widget.

    #     Parameters
    #     ----------
    #     className_moke : str, optional
    #         The className of the Div. Defaults to "grid_layout_xrd".

    #     Returns
    #     -------
    #     children : Dash Div
    #         A Div containing all the components of the XRD widget.
    #     """
    #     children = html.Div(
    #         [
    #             self.folderpath,
    #             self.crange_slider,
    #             self.xrange_slider,
    #             self.yrange_slider,
    #             self.data_type,
    #             self.browse_button,
    #             self.xrd_loop,
    #             self.xrd_heatmap,
    #         ],
    #         className=className_moke,
    #     )

    #     return children

    def make_tab_from_widgets(self):
        """
        Return a dcc.Tab containing all the components of the XRD widget.

        Parameters
        ----------
        id_xrd : str, optional
            The id of the dcc.Tab. Defaults to "xrd".
        label_xrd : str, optional
            The label of the dcc.Tab. Defaults to "XRD".
        value_xrd : str, optional
            The value of the dcc.Tab. Defaults to "xrd".
        className_xrd : str, optional
            The className of the Div containing all the components of the XRD widget.
            Defaults to "grid_layout_xrd".

        Returns
        -------
        xrd_tab : dcc.Tab
            A dcc.Tab containing all the components of the XRD widget.
        """
        xrd_tab = dcc.Tab(
            id="xrd",
            label="XRD",
            value="xrd",
            children=[
                html.Div(
                    children=[
                        dcc.Tab(
                            id="xrd_main",
                            label="XRD",
                            children=[
                                dcc.Loading(
                                    id="loading_xrd_moke",
                                    type="default",
                                    delay_show=500,
                                    children=[
                                        html.Div(
                                            [
                                                self.xrd_left,
                                                self.xrd_center,
                                                self.xrd_right,
                                                self.xrd_heatmap,
                                                self.xrd_pattern,
                                                self.xrd_stores,
                                            ],
                                            className="grid-container",
                                        )
                                    ],
                                )
                            ],
                        )
                    ]
                )
            ],
        )

        return xrd_tab
