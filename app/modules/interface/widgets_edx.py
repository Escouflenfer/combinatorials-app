"""
class file for edx widgets using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import os
from dash import html, dcc


class WidgetsEDX:

    xrange_slider_min = 0
    xrange_slider_max = 20
    xrange_slider_step = 0.1
    xrange_slider_value = [0, 10]
    xrange_slider_markStep = 5

    yrange_slider_min = 0
    yrange_slider_max = 50000
    yrange_slider_step = 1000
    yrange_slider_value = [0, 10000]
    yrange_slider_markStep = 10000

    def __init__(self, folderpath):
        # Folderpath for the EDX spectras
        self.folderpath = folderpath

        self.edx_text_box = dcc.Loading(
        id="loading-1",
        type="default",
        children=html.Div(children=[
            html.Span(children='', id='edx_text_box')
        ]), className='top-center')

        # Heatmap plot options
        self.element = html.Div(className='subgrid top-left', children=[
            html.Div(className='subgrid-2', children=[
                html.Label('Currently plotting:'),
                html.Br(),
                dcc.Dropdown(id="element_edx", className='long-item', options=[], placeholder='Select Element')
            ]),
            html.Div(className='subgrid-7', children=[
                html.Label('Colorbar bounds'),
                dcc.Input(id='edx_heatmap_max', className='long-item', type='number', placeholder='maximum value',
                          value=None),
                dcc.Input(id='edx_heatmap_min', className='long-item', type='number', placeholder='minimum value',
                          value=None)
            ]),
        ])

        # Slider Xrange component
        self.plot_sliders = html.Div(
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
                    className='dropdown-item',
                    id="yrange_slider",
                ),

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
                    className='dropdown-item',
                    id="xrange_slider",
                ),
            ],
            className='top-right',
        )

        # EDX spectra graph that will be modified by user interaction
        self.edx_spectra = html.Div(
            [dcc.Graph(id="edx_spectra")], className='plot-right'
        )

        # EDX heatmap
        self.edx_heatmap = html.Div(
            [dcc.Graph(id="edx_heatmap")], className='plot-left'
        )

        # Stored variables
        self.edx_stores = html.Div(children=[
            dcc.Store(id='edx_position_store'),
            dcc.Store(id='edx_parameters_store'),
        ])

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
                    className='grid-container',
                )
            ],
        )

        return edx_tab
