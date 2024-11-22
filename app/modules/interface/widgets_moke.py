"""
class file for edx widgets using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import os
from dash import html, dcc
import dash_bootstrap_components as dbc
from itertools import count, takewhile


from dash import html, dcc
from natsort import natsorted
import os
import pandas as pd


class WidgetsMOKE:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the center box (text box + database options)
        self.moke_center = html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[html.Span(children="test", id="moke_path_box")],
                ),
                html.Div(
                    className="text-mid",
                    children=[html.Span(children="test", id="moke_text_box")],
                ),
            ],
        )

        # Widget for the left box (heatmap plotting options)
        self.moke_left = html.Div(
            className="subgrid top-left",
            children=[
                html.Div(
                    className="subgrid-2",
                    children=[
                        html.Label("Currently plotting:"),
                        html.Br(),
                        dcc.Dropdown(
                            id="moke_heatmap_select",
                            className="long-item",
                            options=[
                                "Kerr Rotation",
                                "Reflectivity",
                                "Derivative Coercivity",
                                "Measured Coercivity",
                            ],
                            value="Kerr Rotation",
                        ),
                    ],
                ),
                html.Div(
                    className="subgrid-7",
                    children=[
                        html.Label("Colorbar bounds"),
                        dcc.Input(
                            id="moke_heatmap_max",
                            className="long-item",
                            type="number",
                            placeholder="maximum value",
                            value=None,
                        ),
                        dcc.Input(
                            id="moke_heatmap_min",
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
                            id="moke_heatmap_edit",
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

        # Widget for the right box (signal plotting options)
        self.moke_right = html.Div(
            className="subgrid top-right",
            children=[
                html.Div(
                    className="subgrid-1",
                    children=[
                        dcc.Dropdown(
                            id="moke_plot_dropdown", options=[], className="long-item"
                        )
                    ],
                ),
                html.Div(
                    className="subgrid-2",
                    children=[
                        dcc.RadioItems(
                            id="moke_plot_select",
                            options=["Raw data", "Loop", "Loop + Derivative"],
                            value="Loop",
                            style={"display": "inline-block"},
                        )
                    ],
                ),
                html.Div(
                    className="subgrid-3",
                    children=[
                        html.Button(
                            children="Make Loop Map",
                            id="moke_loop_map_button",
                            n_clicks=0,
                        ),
                    ],
                ),
                html.Div(
                    className="subgrid-7",
                    children=[
                        dcc.Checklist(
                            className='long-item',
                            id="moke_data_treatment_checklist",
                            options=[
                                {"label": "Smoothing", "value": "smoothing"},
                                {"label": "Correct offset", "value": "offset"},
                                {"label": "Low field filter", "value": "filter"},
                            ],
                            value=["smoothing", "offset", "filter"],
                        )
                    ]
                ),
                html.Div(
                    className="subgrid-9",
                    id='moke_data_treatment_inputs',
                    children=[
                        html.Label('Smoothing parameters'),
                        html.Label('Polyorder'),
                        dcc.Input(
                            id='moke_smoothing_polyorder',
                            type='number',
                            min=0,
                            step=1,
                        ),
                        html.Label('Range'),
                        dcc.Input(
                            id='moke_smoothing_range',
                            type='number',
                            min=0,
                            step=1
                        )
                    ]
                )
            ],
        )

        # Widget for Moke heatmap
        self.moke_heatmap = html.Div(
            children=[
                dcc.Graph(id="moke_heatmap"),
                html.Button("Save!", id="moke_heatmap_save", n_clicks=0),
            ],
            className="plot-left",
        )

        # Widget for Moke signal
        self.moke_profile = html.Div(
            children=[
                dcc.Graph(id="moke_plot"),
                html.Button("Save!", id="moke_plot_save", n_clicks=0),
            ],
            className="plot-right",
        )

        # Stored variables
        self.moke_stores = html.Div(
            children=[
                dcc.Store(id="moke_position_store", data=None),
                dcc.Store(id="moke_database_path_store", data=None),
                dcc.Store(id="moke_heatmap_replot_tag", data=False),
                dcc.Store(id="moke_database_metadata_store", data=None)
            ]
        )

    def make_tab_from_widgets(self):
        moke_tab = dcc.Tab(
            id="moke",
            label="MOKE",
            value="moke",
            children=[
                html.Div(
                    children=[
                        dcc.Tabs(
                            id="moke_subtabs",
                            value="moke_main",
                            children=[
                                dcc.Tab(
                                    id="moke_main",
                                    label="Main",
                                    children=[
                                        dcc.Loading(
                                            id="loading_main_moke",
                                            type="default",
                                            delay_show=500,
                                            children=[
                                                html.Div(
                                                    [
                                                        self.moke_left,
                                                        self.moke_center,
                                                        self.moke_right,
                                                        self.moke_heatmap,
                                                        self.moke_profile,
                                                        self.moke_stores,
                                                    ],
                                                    className="grid-container",
                                                )
                                            ],
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    id="moke_loop",
                                    label="Loop map",
                                    children=[
                                        dcc.Loading(
                                            id="loading_loop_moke",
                                            type="default",
                                            delay_show=500,
                                            children=[
                                                dcc.Graph(id="moke_loop_map_figure")
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        )
                    ]
                )
            ],
        )

        return moke_tab
