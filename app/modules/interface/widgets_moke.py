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
        self.moke_center = html.Div(className='textbox top-center', children=[
                    html.Div(className='text-top', children=[
                        html.Span(children='test', id='moke_path_box')
                    ]),

                    html.Div(className='text-mid', children=[
                        html.Span(children='test', id='moke_text_box')
                    ]),

                    html.Div(className='text-7', children=[
                        html.Button(children=['Save database'], id='moke_save_button', n_clicks=0)
                    ]),

                    html.Div(className='text-9', children=[
                        html.Button(children=['Reload database'], id='moke_reload_button', n_clicks=0)
                    ])
                ])

        # Widget for the left box (heatmap plotting options)
        self.moke_left = html.Div(className='subgrid top-left', children=[
            html.Div(className='subgrid-2', children=[
                html.Label('Currently plotting:'),
                html.Br(),
                dcc.Dropdown(id='moke_heatmap_select', className='long-item',
                           options=['Kerr Rotation', 'Reflectivity', 'Derivative Coercivity', 'Measured Coercivity'],
                           value='Kerr Rotation'),
            ]),
            html.Div(className='subgrid-7', children=[
                html.Label('Colorbar bounds'),
                dcc.Input(id='moke_heatmap_max', className='long-item', type='number', placeholder='maximum value',
                          value=None),
                dcc.Input(id='moke_heatmap_min', className='long-item', type='number', placeholder='minimum value',
                          value=None)
            ]),
            html.Div(className='subgrid-9', children=[
                html.Label(''),
                html.Br(),
                dcc.RadioItems(
                    id='moke_heatmap_edit',
                    options=[{'label': 'Unfiltered', 'value': 'unfiltered'},
                             {'label': 'Filtered', 'value': 'filter'},
                             {'label': 'Edit mode', 'value': 'edit'}],
                    value='filter',
                    style={'display': 'inline-block'}
                ),
            ])
        ])

        # Widget for the right box (signal plotting options)
        self.moke_right = html.Div(children=[
            dcc.Dropdown(id='moke_plot_dropdown', options=[], className='dropdown-item'),
            dcc.RadioItems(id='moke_plot_select',
                                     options=['Raw data', 'Loop', 'Loop + Derivative'], value='Loop'),
        ], className='top-right')

        # Widget for Moke heatmap
        self.moke_heatmap = html.Div(children=[
            dcc.Graph(id="moke_heatmap"),
            html.Button('Save!', id='moke_heatmap_save', n_clicks=0),
        ], className='plot-left')

        # Widget for Moke signal
        self.moke_profile = html.Div(children=[
            dcc.Graph(id="moke_plot"),
            html.Button('Save!', id='moke_plot_save', n_clicks=0),
        ], className='plot-right')

        # Stored variables
        self.moke_stores = html.Div(children=[
            dcc.Store(id='moke_position_store', data=None),
            dcc.Store(id='moke_database_path_store', data=None),
            dcc.Store(id='moke_heatmap_replot_tag', data=False),
            dcc.Store(id='moke_database_metadata_store', data=None)
        ])



    def make_tab_from_widgets(self):
        moke_tab = dcc.Tab(
            id="moke",
            label="MOKE",
            value="moke",
            children=[html.Div(children=[
                dcc.Loading(
                    id="loading-moke",
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
                                self.moke_stores
                            ],
                            className="grid-container",
                        )

                    ]
                )
            ])]
        )

        return moke_tab
