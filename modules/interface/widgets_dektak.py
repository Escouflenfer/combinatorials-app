"""
Class containing all Dash items and layout information for the DEKTAK tab
"""


from dash import html, dcc
from natsort import natsorted
import os
import pandas as pd

class WidgetsDEKTAK:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the text box
        self.dektak_center = html.Div(className='textbox top-center', children=[
                    html.Div(className='text-top', children=[
                        html.Span(children='test', id='dektak_path_box')
                    ]),

                    html.Div(className='text-mid', children=[
                        html.Span(children='test', id='dektak_text_box')
                    ])
            ])

        # Heatmap plot options
        self.dektak_left = html.Div(className='subgrid top-left', children=[
            html.Div(className='subgrid-2', children=[
                html.Label('Currently plotting:'),
                html.Br(),
                dcc.Dropdown(id='dektak_heatmap_select', className='long-item',
                             options=['Thickness', 'Gradient', 'Standard Deviation'], value='Thickness')
            ]),
            html.Div(className='subgrid-7', children=[
                html.Label('Colorbar bounds'),
                dcc.Input(id='dektak_heatmap_max', className='long-item', type='number', placeholder='maximum value',
                          value=None),
                dcc.Input(id='dektak_heatmap_min', className='long-item', type='number', placeholder='minimum value',
                          value=None)
            ]),
            html.Div(
                className="subgrid-8",
                children=[
                    html.Label("Colorbar precision"),
                    dcc.Input(
                        id="dektak_heatmap_precision",
                        className="long-item",
                        type="number",
                        placeholder="Colorbar precision",
                        value=1,
                    ),
                ]
            ),
            html.Div(className='subgrid-9', children=[
                html.Label(''),
                html.Br(),
                dcc.RadioItems(
                    id='dektak_heatmap_edit',
                    options=[{'label': 'Unfiltered', 'value': 'unfiltered'},
                             {'label': 'Filtered', 'value': 'filter'},
                             {'label': 'Edit mode', 'value': 'edit'}],
                    value='filter',
                    style={'display': 'inline-block'}
                ),
            ])
        ])

        # Widget for fitting parameters and buttons
        self.dektak_right = html.Div(className='subgrid top-right', children=[
            html.Div(className='subgrid-1', children=[
                html.Label('Estimate height'),
                dcc.Input(id='dektak_fit_height', type='number', placeholder='Height estimate', value=None),
                html.Button('Fit!', id='dektak_fit_button', n_clicks=0)
            ]),

            html.Div(className='subgrid-9', children=[
                html.Label('PLACEHOLDER'),
                html.Br(),
                dcc.Checklist(
                    id='dektak_plot_select',
                    options=[{'label': 'Adjustment Slope', 'value': 'Adjustment Slope'},
                             {'label': 'Profile Fits', 'value': 'Profile Fits'}],
                    value='filter',
                    style={'display': 'inline-block'}
                ),
            ])
        ])

        # Stored variables
        self.dektak_stores = html.Div(children=[
            dcc.Store(id='dektak_position_store', data=None),
            dcc.Store(id='dektak_database_path_store', data=None),
            dcc.Store(id='dektak_file_path_store', data=None),
            dcc.Store(id='dektak_parameters_store', data=None),
            dcc.Store(id='dektak_database_metadata_store', data=None)
        ])



    def make_tab_from_widgets(self):
        dektak_tab = dcc.Tab(
            id="dektak",
            label="DEKTAK",
            value="dektak",
            children=[html.Div(children=[
                dcc.Loading(
                    id="loading-dektak",
                    type="default",
                    delay_show=500,
                    children=[
                        html.Div(
                            [
                                self.dektak_left,
                                self.dektak_center,
                                self.dektak_right,
                                self.dektak_heatmap,
                                self.dektak_plot,
                                self.dektak_stores
                            ],
                            className="grid-container",
                        )
                    ]
                )
            ])]
        )

        return dektak_tab

