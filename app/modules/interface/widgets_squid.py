"""
class file for edx widgets using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import os
from dash import html, dcc
from itertools import count, takewhile


from dash import html, dcc
from natsort import natsorted
import os
import pandas as pd

class WidgetsSQUID:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the text box
        self.squid_text_box = html.Div(children=[
            html.Span(children='', id='squid_text_box')
        ], className='cell12')

        # Widget for custom graph options
        self.custom_graph_widget = html.Div(children=[
            html.Label('WIP'),
        ], style={'padding': 10, 'flex': 1}, className='cell_11')

        # Widget for dropdown file list / plot selector
        self.plot_selection_widget = html.Div(children=[
            html.Label('SQUID plot selection'),
            dcc.Dropdown(id='squid_plot_select', options=[]),
        ], style={'padding': 10, 'flex': 1}, className='cell_13')

        # Widget for custom graph
        self.squid_custom = html.Div(children=[
            dcc.Graph(id="squid_custom"),
            html.Button('Save!', id='squid_custom_save', n_clicks=0),
        ], className='plot_cell_left')

        # Widget for SQUID data plot
        self.squid_plot = html.Div(children=[
            dcc.Graph(id="squid_plot"),
            html.Button('Save!', id='squid_plot_save', n_clicks=0),
        ], className='plot_cell_right')

        # Stored variables
        self.squid_stores = html.Div(children=[
            dcc.Store(id='squid_position_store'),
            dcc.Store(id='squid_parameters_store')
        ])



    def make_tab_from_widgets(self):
        moke_tab = dcc.Tab(
            id="squid",
            label="VSM-SQUID",
            value="squid",
            children=[
                html.Div(
                    [
                        self.custom_graph_widget,
                        self.squid_text_box,
                        self.plot_selection_widget,
                        self.squid_custom,
                        self.squid_plot,
                        self.squid_stores
                    ],
                    className="grid_layout_moke",
                )
            ],
        )

        return moke_tab
