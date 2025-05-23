"""
Class containing all Dash items and layout information for the XRD tab
"""

from dash import html, dcc

class WidgetsXRD:
    def __init__(self, folderpath):
        
        # Widget for the text box
        self.xrd_center = (html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[dcc.Dropdown(
                        id="xrd_select_dataset",
                        className="long-item",
                        options=[],
                        value=None,
                    )
                    ],
                ),

                html.Div(className="text-mid", children=[
                    html.Span(children="test", id="xrd_text_box")
                ])
            ]))

        # Heatmap plot options
        self.xrd_left = html.Div(className="subgrid top-left", children=[
            html.Div(className="subgrid-2", children=[
                html.Label("Currently plotting:"),
                html.Br(),
                dcc.Dropdown(id="xrd_heatmap_select", className="long-item", options=[])
            ]),
            html.Div(className="subgrid-7", children=[
                html.Label("Colorbar bounds"),
                dcc.Input(id="xrd_heatmap_max", className="long-item", type="number", placeholder="maximum value",
                          value=None),
                dcc.Input(id="xrd_heatmap_min", className="long-item", type="number", placeholder="minimum value",
                          value=None)
            ]),
            html.Div(
                className="subgrid-8",
                children=[
                    html.Label("Colorbar precision"),
                    dcc.Input(
                        id="xrd_heatmap_precision",
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
                    id="xrd_heatmap_edit",
                    options=[{"label": "Unfiltered", "value": "unfiltered"},
                             {"label": "Filtered", "value": "filter"},
                             {"label": "Edit mode", "value": "edit"}],
                    value="filter",
                    style={"display": "inline-block"}
                ),
            ])
        ])

        # XRD Widget for the right box (XRD spectra plotting)
        self.xrd_right = html.Div(
            className="subgrid top-right",
            children=[

            ],
        )

        # XRD spectra graph that will be modified by user interaction
        self.xrd_plot = html.Div(
            [dcc.Graph(id="xrd_plot")], className="plot-right"
        )

        # XRD heatmap
        self.xrd_heatmap = html.Div(
            [dcc.Graph(id="xrd_heatmap")], className="plot-left"
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


    def make_tab_from_widgets(self):
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
                                    id="loading_xrd",
                                    type="default",
                                    delay_show=500,
                                    children=[
                                        html.Div(
                                            [
                                                self.xrd_left,
                                                self.xrd_center,
                                                self.xrd_right,
                                                self.xrd_heatmap,
                                                self.xrd_plot,
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
