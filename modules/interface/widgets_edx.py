"""
Class containing all Dash items and layout information for the EDX tab
"""

from dash import html, dcc


class WidgetsEDX:

    def __init__(self, folderpath):
        # Folderpath for the EDX spectras
        self.folderpath = folderpath

        self.edx_text_box = dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(children=[html.Span(children="", id="edx_text_box")]),
            className="top-center",
        )

        # Heatmap plot options
        self.element = html.Div(
            className="subgrid top-left",
            children=[
                html.Div(
                    className="subgrid-2",
                    children=[
                        html.Label("Currently plotting:"),
                        html.Br(),
                        dcc.Dropdown(
                            id="element_edx",
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
        self.plot_sliders = html.Div(
            className="top-right",
        )

        # EDX spectra graph that will be modified by user interaction
        self.edx_spectra = html.Div(
            [dcc.Graph(id="edx_spectra")], className="plot-right"
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

    def make_tab_from_widgets(
        self,
        id_edx="edx",
        label_edx="EDX",
        value_edx="edx",
    ):
        edx_tab = dcc.Tab(
            id=id_edx,
            label=label_edx,
            value=value_edx,
            children=[
                html.Div(
                    [
                        self.edx_text_box,
                        self.element,
                        self.plot_sliders,
                        self.edx_heatmap,
                        self.edx_spectra,
                        self.edx_stores,
                    ],
                    className="grid-container",
                )
            ],
        )

        return edx_tab
