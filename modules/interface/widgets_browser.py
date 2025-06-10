from dash import html, dcc
import dash_bootstrap_components as dbc
import os

# "https://github.com/eliasdabbas/dash-file-browser"


class WidgetsBROWSER:
    def __init__(self):

        self.browser = html.Div(
            children=[
                dbc.Row(
                    [
                        dbc.Col(lg=1, sm=1, md=1),
                        dbc.Col(
                            [
                                dcc.Store(id="stored_cwd", data=os.getcwd()),
                                html.Hr(),
                                html.Br(),
                                html.H4(
                                    html.B(
                                        html.A(
                                            "⬆️ Parent directory",
                                            href="#",
                                            id="parent_dir",
                                        )
                                    )
                                ),
                                html.H3([html.Code(os.getcwd(), id="cwd")]),
                                html.Br(),
                                html.Br(),
                                html.Div(
                                    id="cwd_files",
                                    style={"height": 500, "overflow": "scroll"},
                                ),
                            ],
                            width=8,
                            style={"position": "relative"},
                        ),
                    ]
                )
            ]
        )

        self.folder_path_store = html.Div(
            children=[
                dcc.Store(id="data_path_store", storage_type="local"),
                dcc.Store(id="edx_path_store", storage_type="local"),
                dcc.Store(id="dektak_path_store", storage_type="local"),
                dcc.Store(id="moke_path_store", storage_type="local"),
                dcc.Store(id="xrd_path_store", storage_type="local"),
                dcc.Store(id="hdf5_path_store", storage_type="local"),
            ]
        )

        self.make_folder_button = html.Div(
            children=[
                html.Button("Set data folder", id="data_path_button"),
                html.Div(
                    "No path set",
                    id="data_path_text",
                    style={"display": "inline-block", "margin-left": "10px"},
                ),
            ],
            style={"display": "flex", "align-items": "center"},
        )

        self.make_hdf5_button = html.Div(
            children=[
                html.Button("Set HDF5 folder", id="hdf5_path_button"),
                html.Div(
                    "None",
                    id="hdf5_path_text",
                    style={"display": "inline-block", "margin-left": "10px"},
                ),
            ],
            style={"display": "flex", "align-items": "center"},
        )


    def make_tab_from_widgets(self):
        browser_tab = dcc.Tab(
            id="browser",
            label="BROWSER",
            value="browser",
            children=[
                html.Div(
                    [
                        self.make_folder_button,
                        self.make_hdf5_button,
                        self.browser,
                        self.folder_path_store,
                    ],
                )
            ],
        )

        return browser_tab
