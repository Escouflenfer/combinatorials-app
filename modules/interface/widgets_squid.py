"""
Class containing all Dash items and layout information for the SQUID tab
"""

from dash import html, dcc


class WidgetsSQUID:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the text box
        self.squid_text_box = html.Div(children=[
            html.Span(children='', id='squid_text_box')
        ], className='cell12')

        # Widget for custom graph options
        self.squid_custom_options = html.Div(children=[
            html.Label('WIP'),
        ], style={'padding': 10, 'flex': 1}, className='cell_11')

        # Widget for dropdown file list / plot selector
        self.squid_plot_select = html.Div(children=[
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
                        self.squid_custom_options,
                        self.squid_text_box,
                        self.squid_plot_select,
                        self.squid_custom,
                        self.squid_plot,
                        self.squid_stores
                    ],
                    className="grid_layout_moke",
                )
            ],
        )

        return moke_tab
