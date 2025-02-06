from dash import html, dcc

class WidgetsHDF5:

    def __init__(self, folderpath):
        self.folderpath = folderpath

        # Widget for the drag and drop
        self.hdf5_left = html.Div(
            className='',
            children=[
                html.Div([
                    dcc.Upload(
                        id='hdf5_upload',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ])
                    ),
                ])
            ],
        )

        # Widget for the center box (text box + database options)
        self.hdf5_center = html.Div(
            className="textbox top-center",
            children=[
                html.Div(
                    className="text-top",
                    children=[html.Span(children="test", id="hdf5_path_box")],
                ),
                html.Div(
                    className="text-mid",
                    children=[html.Span(children="test", id="hdf5_text_box")],
                ),
                html.Div(
                    className="text-9",
                    children=[
                        html.Button(id='hdf5_reset', children="Reset Changes", n_clicks=0),
                        html.Button(id='hdf5_save', children="Save Changes", n_clicks=0)
                        ],
                ),
                html.Div(
                    className='text-7',
                    children=[html.Button(id='hdf5_new', children="Create new HDF5", n_clicks=0)]
                )
            ],
        )


    def make_tab_from_widgets(self):
        hdf5_tab = dcc.Tab(
            id='hdf5',
            label='HDF5',
            value='hdf5',
            children=[
                html.Div(
                    [
                        self.hdf5_left,
                        self.hdf5_center,
                    ],
                    className="grid-container",
                )
            ],
        )

        return hdf5_tab