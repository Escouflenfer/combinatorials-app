"""
Class containing all Dash items and layout information for the profil tab
"""
from dash import html, dcc


class WidgetsPROFIL:
    def __init__(self):

        # Widget for the text box
        self.profil_center = (html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[dcc.Dropdown(
                        id="profil_select_dataset",
                        className="long-item",
                        options=[],
                        value=None,
                    )
                    ],
                ),

                html.Div(className="text-mid", children=[
                    html.Span(children="test", id="profil_text_box")
                ])
            ]))

        # Heatmap plot options
        self.profil_left = html.Div(className="subgrid top-left", children=[
            html.Div(className="subgrid-2", children=[
                html.Label("Currently plotting:"),
                html.Br(),
                dcc.Dropdown(id="profil_heatmap_select", className="long-item", options=[])
            ]),
            html.Div(className="subgrid-7", children=[
                html.Label("Colorbar bounds"),
                dcc.Input(id="profil_heatmap_max", className="long-item", type="number", placeholder="maximum value",
                          value=None),
                dcc.Input(id="profil_heatmap_min", className="long-item", type="number", placeholder="minimum value",
                          value=None)
            ]),
            html.Div(
                className="subgrid-8",
                children=[
                    html.Label("Colorbar precision"),
                    dcc.Input(
                        id="profil_heatmap_precision",
                        className="long-item",
                        type="number",
                        placeholder="Colorbar precision",
                        value=1,
                    ),
                ]
            ),
            html.Div(className="subgrid-9", children=[
                html.Label(""),
                html.Br(),
                dcc.RadioItems(
                    id="profil_heatmap_edit",
                    options=[{"label": "Unfiltered", "value": "unfiltered"},
                             {"label": "Filtered", "value": "filter"},
                             {"label": "Edit mode", "value": "edit"}],
                    value="filter",
                    style={"display": "inline-block"}
                ),
            ])
        ])

        # Widget for fitting parameters and buttons
        self.profil_right = html.Div(className="subgrid top-right", children=[
            html.Div(className="subgrid-1", children=[
                html.Label("Select mode"),
                dcc.Dropdown(id="profil_select_fit_mode", className="long-item",
                             options=["Spot fitting", "Batch fitting", "Manual"], value="Spot fitting")
            ]),

            html.Div(className="subgrid-2", id="profil_fit_inputs", children=[

            ]),

            html.Div(
                className="subgrid-3", children=[
                    html.Button(children="Go", id="profil_fit_button", className="long-item", n_clicks=0)
                ]
            ),

            html.Div(className="subgrid-9", children=[
                html.Label("Plot Options"),
                html.Br(),
                dcc.Checklist(
                    id="profil_plot_select",
                    options=[{"label": "Adjusting Slope", "value": "adjusting_slope"},
                             {"label": "Profile Fits", "value": "fit_parameters"},],
                    value=["adjusting_slope", "profile_fits"],
                    style={"display": "inline-block"}
                ),
            ])
        ])

        # EDX spectra graph that will be modified by user interaction
        self.profil_plot = html.Div(
            [dcc.Graph(id="profil_plot")], className="plot-right"
        )

        # EDX heatmap
        self.profil_heatmap = html.Div(
            [dcc.Graph(id="profil_heatmap")], className="plot-left"
        )

        # Stored variables
        self.profil_stores = html.Div(children=[
            dcc.Store(id="profil_position_store", data=None),
            dcc.Store(id="profil_database_path_store", data=None),
            dcc.Store(id="profil_file_path_store", data=None),
            dcc.Store(id="profil_parameters_store", data=None),
            dcc.Store(id="profil_database_metadata_store", data=None)
        ])



    def make_tab_from_widgets(self):
        profil_tab = dcc.Tab(
            id="profil",
            label="PROFIL",
            value="profil",
            children=[html.Div(children=[
                dcc.Loading(
                    id="loading-profil",
                    type="default",
                    delay_show=500,
                    children=[
                        html.Div(
                            [
                                self.profil_left,
                                self.profil_center,
                                self.profil_right,
                                self.profil_heatmap,
                                self.profil_plot,
                                self.profil_stores
                            ],
                            className="grid-container",
                        )
                    ]
                )
            ])]
        )

        return profil_tab

