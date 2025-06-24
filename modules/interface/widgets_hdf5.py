from dash import html, dcc
import dash_uploader as du

class WidgetsHDF5:

    def __init__(self, upload_folder_root):
        self.upload_folder_root = upload_folder_root

        # Widget for the drag and drop
        self.hdf5_left = html.Div(
            className='textbox top-left',
            children=[
                html.Div(
                    className='text-top',
                    children=[
                    du.Upload(
                        id='hdf5_upload',
                        text='Drag and Drop or click to browse',
                        filetypes=['zip', 'h5', 'hdf5'],
                        upload_id='temp',
                    ),
                ]),
                html.Div(
                    className='text-mid',
                    id="hdf5_dataset_input",
                    children=[
                        html.Label("Dataset Name"),
                        dcc.Input(
                            id="hdf5_dataset_name",
                            className="long-item",
                            type="text",
                            placeholder="Dataset Name",
                            value=None
                        )
                    ]
                ),
                html.Div(
                    className='text-7',
                    children=[html.Button(id='hdf5_add_button', children='Add measurement', n_clicks=0)]
                ),
                html.Div(
                    className='text-9',
                    children=[dcc.Dropdown(className='long-item',
                                           id='hdf5_measurement_type',
                                           options=['EDX', 'PROFIL', 'MOKE', 'XRD', "ESRF", "XRD results"],
                                           value=None)]
                )
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
                    className='text-7',
                    children=[html.Button(id='hdf5_new', children="Create new HDF5", n_clicks=0)]
                ),
                html.Div(
                    className='text-8',
                    children=[html.Button(id='hdf5_update', children="Update HDF5 structure", n_clicks=0)]
                ),
                html.Div(
                    className='text-9',
                    children=[html.Button(id='hdf5_export', children="Export to CSV", n_clicks=0)]
                ),
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
                            id='hdf5_sample_date',
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
                            id='hdf5_sample_operator',
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
                dcc.Store(id="hdf5_upload_folder_root", data=upload_folder_root),
                dcc.Store(id="hdf5_upload_folder_path", data=None),
            ]
        )


    def make_tab_from_widgets(self):
        hdf5_tab = dcc.Tab(
            id='hdf5',
            label='HDF5',
            value='hdf5',
            children=[html.Div(children=[
                dcc.Loading(
                    id="loading-hdf5",
                    type="default",
                    delay_show=500,
                    children=[
                html.Div(
                    [
                        self.hdf5_left,
                        self.hdf5_center,
                        self.hdf5_right,
                        self.hdf5_stores,
                    ],
                    className="grid-container",
                )
                ])
            ])]
        )

        return hdf5_tab