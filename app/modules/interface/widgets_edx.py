"""
class file for edx widgets using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import os
from dash import html, dcc


class WidgetsEDX:
    folderpath_className = "cell12"

    element_className = "cell22"

    xrange_slider_min = 0
    xrange_slider_max = 20
    xrange_slider_step = 0.1
    xrange_slider_value = [0, 10]
    xrange_slider_markStep = 5
    xrange_slider_className = "cell13"

    yrange_slider_min = 0
    yrange_slider_max = 50000
    yrange_slider_step = 1000
    yrange_slider_value = [0, 10000]
    yrange_slider_markStep = 10000
    yrange_slider_className = "cell23"

    crange_slider_min = 0
    crange_slider_max = 100
    crange_slider_step = 0.1
    crange_slider_value = [0, 100]
    crange_slider_markStep = 5
    crange_slider_className = "cell11"

    edx_spectra_className = "plot_cell_right"

    edx_heatmap_className = "plot_cell_left"

    def __init__(self, folderpath):
        # Folderpath for the EDX spectras
        self.folderpath = folderpath

        # Element component
        self.element = html.Div(
            children=[html.Label("Element"), dcc.Dropdown([], id="element_edx")],
            className=self.element_className,
        )

        # Slider Xrange component
        self.xrange_slider = html.Div(
            children=[
                html.Label("Energy Range"),
                dcc.RangeSlider(
                    min=self.xrange_slider_min,
                    max=self.xrange_slider_max,
                    step=self.xrange_slider_step,
                    value=self.xrange_slider_value,
                    marks={
                        i: f"{i}"
                        for i in range(
                            self.xrange_slider_min,
                            self.xrange_slider_max + self.xrange_slider_markStep,
                            self.xrange_slider_markStep,
                        )
                    },
                    id="xrange_slider",
                ),
            ],
            className=self.xrange_slider_className,
        )

        # Slider Yrange component
        self.yrange_slider = html.Div(
            children=[
                html.Label("Counts"),
                dcc.RangeSlider(
                    min=self.yrange_slider_min,
                    max=self.yrange_slider_max,
                    step=self.yrange_slider_step,
                    value=self.yrange_slider_value,
                    marks={
                        i: f"{i}"
                        for i in range(
                            self.yrange_slider_min,
                            self.yrange_slider_max + self.yrange_slider_markStep,
                            self.yrange_slider_markStep,
                        )
                    },
                    id="yrange_slider",
                ),
            ],
            className=self.yrange_slider_className,
        )

        # Colorange for heatmap
        self.crange_slider = html.Div(
            children=[
                html.Label("Color Range"),
                dcc.RangeSlider(
                    min=self.crange_slider_min,
                    max=self.crange_slider_max,
                    step=self.crange_slider_step,
                    value=self.crange_slider_value,
                    marks={
                        i: f"{i}"
                        for i in range(
                            self.crange_slider_min,
                            self.crange_slider_max + self.crange_slider_markStep,
                            self.crange_slider_markStep,
                        )
                    },
                    id="crange_slider",
                ),
            ],
            className=self.crange_slider_className,
        )

        # EDX spectra graph that will be modified by user interaction
        self.edx_spectra = html.Div(
            [dcc.Graph(id="edx_spectra")], className=self.edx_spectra_className
        )

        # EDX heatmap
        self.edx_heatmap = html.Div(
            [dcc.Graph(id="edx_heatmap")], className=self.edx_heatmap_className
        )

    def make_tab_from_widgets(
        self,
        id_edx="edx",
        label_edx="EDX",
        value_edx="edx",
        className_edx="grid_layout_edx",
    ):
        edx_tab = dcc.Tab(
            id=id_edx,
            label=label_edx,
            value=value_edx,
            children=[
                html.Div(
                    [
                        self.folderpath,
                        self.element,
                        self.crange_slider,
                        self.xrange_slider,
                        self.yrange_slider,
                        self.edx_heatmap,
                        self.edx_spectra,
                    ],
                    className=className_edx,
                )
            ],
        )

        return edx_tab
