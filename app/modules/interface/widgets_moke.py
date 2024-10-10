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

        # Widget for the text box
        self.moke_text_box = dcc.Loading(
        id="loading-moke",
        type="default",
        children=html.Div(children=[
            html.Span(children='', id='moke_text_box')
        ]), className='top-center')

        # Widget Heatmap plot option radio items
        self.heatmap_selection_widget = html.Div(className='subgrid top-left', children=[
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

        ])

        # Widget plotting options
        self.plot_selection_widget = html.Div(children=[
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
            dcc.Store(id='moke_parameters_store', data=None)
        ])



    def make_tab_from_widgets(self):
        moke_tab = dcc.Tab(
            id="moke",
            label="MOKE",
            value="moke",
            children=[
                html.Div(
                    [
                        self.heatmap_selection_widget,
                        self.moke_text_box,
                        self.plot_selection_widget,
                        self.moke_heatmap,
                        self.moke_profile,
                        self.moke_stores
                    ],
                    className="grid-container",
                )
            ],
        )

        return moke_tab
