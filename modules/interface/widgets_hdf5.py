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

        # Widget for the right box (sample info)
        self.hdf5_right = html.Div(
            className="subgrid top-right",
            children=[
                html.Div(
                    className="subgrid-1",
                    children=[
                        html.Label("Fabrication date"),
                        dcc.Input(
                            className="long-item",
                            id='hdf5_fabrication_date',
                            type='text',
                            placeholder='Fabrication date'
                        ),
                        html.Label("Sample Name"),
                        dcc.Input(
                            className="long-item",
                            id='hdf5_sample_name',
                            type='text',
                            placeholder='Sample name'
                        ),
                        html.Label("Operator Name"),
                        dcc.Input(
                            className="long-item",
                            id='hdf5_operator_name',
                            type='text',
                            placeholder='Operator name'
                        )
                    ]
                ),
                html.Div(
                    className="subgrid-3",
                    children=[
                            dcc.Dropdown(
                                className='long-item',
                                id="hdf5_layer_dropdown",
                                options=['Add layer']
                            ),
                        html.Div(children=[
                            dcc.Input(
                                id="hdf5_layer_element",
                                type='text',
                                placeholder='Layer element',
                                debounce=True
                            ),
                            dcc.Input(
                                id="hdf5_layer_thickness",
                                type='number',
                                placeholder='Layer thickness',
                                debounce=True
                            )],
                        style={'display': 'flex', 'gap': '10px'}
                        )
                    ]
                )
            ]
        )

        # Stored variables
        self.hdf5_stores = html.Div(
            children=[
                dcc.Store(id="hdf5_layer_structure_store", data=None),
            ]
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
                        self.hdf5_right,
                    ],
                    className="grid-container",
                )
            ],
        )

        return hdf5_tab