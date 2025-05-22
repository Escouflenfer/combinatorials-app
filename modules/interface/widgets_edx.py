"""
Class containing all Dash items and layout information for the EDX tab
"""

from dash import html, dcc


class WidgetsEDX:
    def __init__(self):

        # Widget for the text box
        self.edx_center = (html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[dcc.Dropdown(
                        id="edx_select_dataset",
                        className="long-item",
                        options=[],
                        value=None,
                    )
                    ],
                ),

                html.Div(className="text-mid", children=[
                    html.Span(children="test", id="edx_text_box")
                ])
            ]))

        # Heatmap plot options
        self.edx_left = html.Div(
            className="subgrid top-left",
            children=[
                html.Div(
                    className="subgrid-2",
                    children=[
                        html.Label("Currently plotting:"),
                        html.Br(),
                        dcc.Dropdown(
                            id="edx_heatmap_select",
                            className="long-item",
                            options=[],
                            placeholder="Select Element",
                        ),
                    ],
                ),
                html.Div(
                    className="subgrid-7",
                    children=[
                        html.Label("Colorbar bounds"),
                        dcc.Input(
                            id="edx_heatmap_max",
                            className="long-item",
                            type="number",
                            placeholder="maximum value",
                            value=None,
                        ),
                        dcc.Input(
                            id="edx_heatmap_min",
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
                            id="edx_heatmap_precision",
                            className="long-item",
                            type="number",
                            placeholder="Colorbar precision",
                            value=2,
                        ),
                    ]
                )
            ],
        )

        # Slider Xrange component
        self.edx_right = html.Div(
            className="top-right",
        )

        # EDX plot
        self.edx_plot = html.Div(
            [dcc.Graph(id="edx_plot")], className="plot-right"
        )

        # EDX heatmap
        self.edx_heatmap = html.Div(
            [dcc.Graph(id="edx_heatmap")], className="plot-left"
        )

        # Stored variables
        self.edx_stores = html.Div(
            children=[
                dcc.Store(id="edx_position_store"),
                dcc.Store(id="edx_parameters_store"),
            ]
        )

    def make_tab_from_widgets(self):
        edx_tab = dcc.Tab(
            id="edx",
            label="EDX",
            value="edx",
            children=[html.Div(children=[
                dcc.Loading(
                    id="loading_edx",
                    type="default",
                    delay_show=500,
                    children=[
                        html.Div(
                            [
                                self.edx_left,
                                self.edx_center,
                                self.edx_right,
                                self.edx_heatmap,
                                self.edx_plot,
                                self.edx_stores
                            ],
                            className="grid-container",
                        )
                    ]
                )
            ])]
        )

        return edx_tab
