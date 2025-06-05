"""
Class containing all Dash items and layout information for the MOKE tab
"""

from dash import html, dcc



class WidgetsMOKE:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the center box (text box + database options)
        self.moke_center = html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[dcc.Dropdown(
                        id="moke_select_dataset",
                        className="long-item",
                        options=[],
                        value=None,
                    )
                    ],
                ),
                html.Div(
                    className="text-mid",
                    children=[html.Span(children="test", id="moke_text_box")],
                ),
                html.Div(
                    className="text_8",
                    children=[html.Button(id='moke_make_database_button', children="Make database!", n_clicks=0)],
                )
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
                            options=[]
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
                    className="subgrid-8",
                    children=[
                        html.Label("Colorbar precision"),
                        dcc.Input(
                            id="moke_heatmap_precision",
                            className="long-item",
                            type="number",
                            placeholder="Colorbar precision",
                            value=1,
                        ),
                    ]
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
                            options=[
                                {"label": "Oscilloscope Data", "value": "oscilloscope"},
                                {"label": "M(H) Loop", "value": "loop"},
                                {"label": "M(H) Loop + Stored Result", "value": "stored_result"},
                                {"label": "M(H) Loop + Live Result", "value": "live_result"},
                            ],
                            value="loop",
                            style={"display": "inline-block"},
                        )
                    ],
                ),
                html.Div(
                    className="subgrid-4",
                    children=[
                        html.Label('Coil Factor (T/100V)'),
                        dcc.Input(
                            className='long-item',
                            id='moke_coil_factor',
                            type='number',
                            min=0,
                            step=0.00001
                        )
                    ]
                ),
                html.Div(
                    className="subgrid-7",
                    children=[
                        dcc.Checklist(
                            className='long-item',
                            id="moke_data_treatment_checklist",
                            options=[
                                {"label": "Smoothing", "value": "smoothing"},
                                {"label": "Correct offset", "value": "correct_offset"},
                                {"label": "Low field filter", "value": "filter_zero"},
                                {"label": "Connect loops", "value": "connect_loops"},
                            ],
                            value=["smoothing", "correct_offset", "filter_zero", "connect_loops"],
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
                            className='long-item',
                            id='moke_smoothing_polyorder',
                            type='number',
                            min=0,
                            step=1,
                        ),
                        html.Label('Range'),
                        dcc.Input(
                            className='long-item',
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
            ],
            className="plot-left",
        )

        # Widget for Moke signal
        self.moke_profile = html.Div(
            children=[
                dcc.Graph(id="moke_plot"),
            ],
            className="plot-right",
        )

        # Stored variables
        self.moke_stores = html.Div(
            children=[
                dcc.Store(id="moke_position_store", data=None),
                dcc.Store(id="moke_database_path_store", data=None),
                dcc.Store(id="moke_database_metadata_store", data=None),
                dcc.Store(id="moke_data_treatment_store", data=None),
                dcc.Store(id="moke_initial_load_trigger", data="load")
            ]
        )

        # Loop map tab

        # Widget for the loop map graph
        self.moke_loop_map_figure = html.Div(
            children=[
                dcc.Graph(id="moke_loop_map_figure"),
            ],
            className='loop-map'
        )

        # Widget for the options on the loop map tab
        self.moke_loop_map_options = html.Div(
            className='column-subgrid loop-options',
            children=[
                html.Button(
                    className='column-1 long-item',
                    children="Make Loop Map",
                    id="moke_loop_map_button",
                    n_clicks=0,
                ),
                dcc.Checklist(
                    className='long-item',
                    id="moke_loop_map_checklist",
                    options=[
                        {"label": "Normalize", "value": "normalize"}
                    ],
                    value=[],
                ),
            ]
        )

    def make_tab_from_widgets(self):
        moke_tab = dcc.Tab(
            id="moke",
            label="MOKE",
            value="moke",
            children=[
                self.moke_stores,
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
                                                    children=[
                                                        self.moke_left,
                                                        self.moke_center,
                                                        self.moke_right,
                                                        self.moke_heatmap,
                                                        self.moke_profile,
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
                                                html.Div(
                                                    children=[
                                                        self.moke_loop_map_figure,
                                                        self.moke_loop_map_options,
                                                    ],
                                                    className="grid-container",
                                                )
                                            ],
                                        )
                                    ],
                                )
                            ],
                        )
                    ]
                )
            ],
        )

        return moke_tab
