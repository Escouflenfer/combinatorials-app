from dash import html, dcc
import dash_bootstrap_components as dbc
import os

class WidgetsBROWSER:
    def __init__(self):

        self.browser = html.Div(children=[
        html.Link(
            rel="stylesheet",
            href="https://cdnjs.cloudflare.com/ajax/libs/github-fork-ribbon-css/0.2.3/gh-fork-ribbon.min.css"),
        html.A(
            className="github-fork-ribbon",
            href="https://github.com/eliasdabbas/dash-file-browser",
            title="Original on Github", **{"data-ribbon": "Original on Github"}),
        html.Br(), html.Br(),
        dbc.Row([
            dbc.Col(lg=1, sm=1, md=1),

            dbc.Col([
                dcc.Store(id='stored_cwd', data=os.getcwd()),
                html.Hr(), html.Br(),
                html.H4(html.B(html.A("⬆️ Parent directory", href='#',
                                      id='parent_dir'))),

                html.H3([html.Code(os.getcwd(), id='cwd')]),
                html.Br(), html.Br(),

                html.Div(id='cwd_files', style={'height': 500, 'overflow': 'scroll'}),
            ], width=8, style={'position': 'relative'}),
            ])
        ])

        self.folder_path_store = html.Div(children=[
            dcc.Store(id='data_path_store', storage_type='local'),
            dcc.Store(id='edx_path_store', storage_type='local'),
            dcc.Store(id='dektak_path_store', storage_type='local'),
            dcc.Store(id='moke_path_store', storage_type='local'),
            dcc.Store(id='xray_path_store', storage_type='local'),
            dcc.Store(id='squid_path_store', storage_type='local')
        ])

        self.make_folder_button = html.Div(children=[
            html.Button('Set data folder', id='data_path_button'),
            html.Div('No path set', id='data_path_text', style={'display': 'inline-block', 'margin-left': '10px'})
            ], style={'display': 'flex', 'align-items': 'center'})

        self.make_edx_button = html.Div(children=[
            html.Button('Set EDX folder', id='edx_path_button'),
            html.Div('No path set', id='edx_path_text', style={'display': 'inline-block', 'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center'})

        self.make_dektak_button = html.Div(children=[
            html.Button('Set DEKTAK folder', id='dektak_path_button'),
            html.Div('No path set', id='dektak_path_text', style={'display': 'inline-block', 'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center'})

        self.make_moke_button = html.Div(children=[
            html.Button('Set MOKE folder', id='moke_path_button'),
            html.Div('No path set', id='moke_path_text', style={'display': 'inline-block', 'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center'})

        self.make_xray_button = html.Div(children=[
            html.Button('Set XRAY folder', id='xray_path_button'),
            html.Div('No path set', id='xray_path_text', style={'display': 'inline-block', 'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center'})

        self.make_squid_button = html.Div(children=[
            html.Button('Set SQUID folder', id='SQUID_path_button'),
            html.Div('No path set', id='squid_path_text', style={'display': 'inline-block', 'margin-left': '10px'})
        ], style={'display': 'flex', 'align-items': 'center'})



    def make_tab_from_widgets(self):
        browser_tab = dcc.Tab(
            id="browser",
            label="BROWSER",
            value="browser",
            children=[
                html.Div(
                    [
                        self.make_folder_button,
                        self.make_edx_button,
                        self.make_dektak_button,
                        self.make_moke_button,
                        self.make_xray_button,
                        self.make_squid_button,
                        self.browser,
                        self.folder_path_store

                    ],
                )
            ],
        )

        return browser_tab