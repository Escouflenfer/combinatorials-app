from dash import html, dcc
from natsort import natsorted
import os
import pandas as pd

class WidgetsDEKTAK:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the text box
        self.dektak_text_box = html.Div(children=[
            html.Span(children='', id='dektak_text_box')
        ], className='cell12')

        # Widget Heatmap plot option radio items
        self.heatmap_selection_widget = html.Div(children=[
            html.Label('Heatmap plot selection'),
            dcc.RadioItems(id='dektak_heatmap_select', options=['Thickness', 'Gradient', 'Standard Deviation'], value='Thickness'),
        ], style={'padding': 10, 'flex': 1}, className='cell_11')

        # Widget for fitting parameters and button
        self.fitting_widget = html.Div(id='dektak_fit_interface', children=[
            dcc.Input(id='dektak_fit_start', type='number', placeholder='First step up position', value=None),
            dcc.Input(id='dektak_fit_height', type='number', placeholder='Height estimate', value=None),
            dcc.Input(id='dektak_fit_stepnb', type='number', placeholder='Number of steps', value=None),
            html.Button('Fit!', id='dektak_fit_button', n_clicks=0),
            html.Button('Save', id='dektak_save_button', n_clicks=0),
            html.Button('Clear', id='dektak_clear_button', n_clicks=0)
        ], className='cell_13')

        # Widget for Dektak heatmap
        self.dektak_heatmap = html.Div(children=[
            dcc.Graph(id="dektak_heatmap"),
            html.Button('Save!', id='dektak_heatmap_save', n_clicks=0),
        ], className='plot_cell_left')

        # Widget for Dektak profile plot
        self.dektak_plot = html.Div(children=[
            dcc.Graph(id="dektak_plot"),
            html.Button('Save!', id='dektak_plot_save', n_clicks=0),
        ], className='plot_cell_right')

        # Stored variables
        self.dektak_stores = html.Div(children=[
            dcc.Store(id='dektak_position_store'),
            dcc.Store(id='dektak_parameters_store'),
        ])



    def make_tab_from_widgets(self):
        dektak_tab = dcc.Tab(
            id="dektak",
            label="DEKTAK",
            value="dektak",
            children=[
                html.Div(
                    [
                        self.heatmap_selection_widget,
                        self.dektak_text_box,
                        self.fitting_widget,
                        self.dektak_heatmap,
                        self.dektak_plot,
                        self.dektak_stores
                    ],
                    className="grid_layout_dektak",
                )
            ],
        )

        return dektak_tab

