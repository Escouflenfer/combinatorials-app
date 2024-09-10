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

class WidgetsMOKE:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the text box
        self.moke_text_box = html.Div(children=[
            html.Span(children='', id='moke_text_box')
        ], className='cell12')

        # Widget Heatmap plot option radio items
        self.heatmap_selection_widget = html.Div(children=[
            html.Label('Heatmap plot selection'),
            dcc.RadioItems(id='moke_heatmap_select', options=['Blank', 'Coercivity', 'Reflectivity'], value='Blank'),
        ], style={'padding': 10, 'flex': 1}, className='cell_11')

        # Widget plotting options
        self.plot_selection_widget = html.Div(children=[
            html.Label('Plot selection'),
            dcc.RadioItems(id='moke_plot_select', options=['Raw data', 'Loop'], value='Loop'),
            dcc.Dropdown(id='moke_plot_dropdown', options=[]),
        ], style={'padding': 10, 'flex': 1}, className='cell_13')

        # Widget for Moke heatmap
        self.moke_heatmap = html.Div(children=[
            dcc.Graph(id="moke_heatmap"),
            html.Button('Save!', id='moke_heatmap_save', n_clicks=0),
        ], className='plot_cell_left')

        # Widget for Moke signal
        self.moke_profile = html.Div(children=[
            dcc.Graph(id="moke_plot"),
            html.Button('Save!', id='moke_plot_save', n_clicks=0),
        ], className='plot_cell_right')

        # Stored variables
        self.moke_stores = html.Div(children=[
            dcc.Store(id='moke_position_store'),
            dcc.Store(id='moke_parameters_store')
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
                    className="grid_layout_moke",
                )
            ],
        )

        return moke_tab
