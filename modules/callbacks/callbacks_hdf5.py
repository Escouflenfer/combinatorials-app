from dash import Input, Output, State, ctx, html, dcc
from dash.exceptions import PreventUpdate
import zipfile

from ..functions.functions_shared import *
from ..hdf5_compilers.hdf5compile_base import *
from ..hdf5_compilers.hdf5compile_edx import *
from ..hdf5_compilers.hdf5compile_esrf import write_esrf_to_hdf5, write_xrd_results_to_hdf5
from ..hdf5_compilers.hdf5compile_moke import *
from ..hdf5_compilers.hdf5compile_profil import *
from ..hdf5_compilers.hdf5compile_xrd import *


def callbacks_hdf5(app):

    @app.callback([Output('hdf5_path_box', 'children'),
                   Output('hdf5_text_box', 'children')],
                  Input('hdf5_new', 'n_clicks'),
                  State('data_path_store', 'data'),
                  State('hdf5_sample_name', 'value'),
                  State('hdf5_sample_date', 'value'),
                  State('hdf5_sample_operator', 'value'),
                  State('hdf5_layer_dropdown', 'options'),
                  )

    def create_new_hdf5_file(n_clicks, data_path, sample_name, sample_date, sample_operator, layer_dropdown):
        if n_clicks > 0:

            sample_dict = {
                'sample_name': sample_name,
                'fabrication_date': sample_date,
                'operator': sample_operator
            }

            layer_dropdown.remove('Add layer')
            try:
                for idx, layer in enumerate(layer_dropdown):
                    match = re.split(r'\s*\(\s*|\s*\)\s*', layer)
                    sample_dict[f'layer {idx}'] = {'Element' :  match[0], 'Thickness' : match[1]}
            except TypeError:
                return '', 'At least one layer is necessary to create new file'

            if not all(sample_dict.values()):
                return '', 'All data entries must be filled to create a new hdf5 file'

            data_path = Path(data_path)
            hdf5_path = data_path / f'{sample_name}.hdf5'
            check = create_new_hdf5(hdf5_path, sample_dict)
            if check:
                return str(hdf5_path), f'Created new HDF5 file at {hdf5_path}'
        else:
            raise PreventUpdate



    # Callback to add new layers to the film
    @app.callback(
        [Output('hdf5_layer_dropdown', 'value', allow_duplicate=True),
         Output('hdf5_layer_dropdown', 'options', allow_duplicate=True)],
        Input('hdf5_layer_dropdown', 'value'),
        State('hdf5_layer_dropdown', 'options'),
        prevent_initial_call=True
    )
    def update_layer_dropdown(dropdown_value, dropdown_options):
        if dropdown_value == 'Add layer':
            dropdown_options.append('New layer')
            return 'New layer', dropdown_options
        else:
            raise PreventUpdate


    # Callback to set layer attributes
    @app.callback(
        [Output('hdf5_layer_dropdown', 'options', allow_duplicate=True),
        Output('hdf5_layer_dropdown', 'value', allow_duplicate=True)],
        Input('hdf5_layer_element', 'value'),
        Input('hdf5_layer_thickness', 'value'),
        State('hdf5_layer_dropdown', 'value'),
        State('hdf5_layer_dropdown', 'options'),
        prevent_initial_call=True
    )
    def update_layer_attributes(layer_element, layer_thickness, dropdown_value, dropdown_options):
        if dropdown_value != 'Add layer':
            layer_details = f'{layer_element} ({layer_thickness} nm)'
            dropdown_options.remove(dropdown_value)
            dropdown_options.append(layer_details)
            return dropdown_options, layer_details
        else:
            raise PreventUpdate


    @app.callback(
        Output('hdf5_text_box', 'children', allow_duplicate=True),
        Input('hdf5_add_button', 'n_clicks'),
        State('hdf5_upload_folder_path', 'data'),
        State('hdf5_measurement_type', 'value'),
        State('hdf5_path_store', 'data'),
        State("hdf5_dataset_name", "value"),
        prevent_initial_call=True
    )

    def add_measurement_to_file(n_clicks, uploaded_folder_path, measurement_type, hdf5_path, dataset_name):
        if n_clicks > 0:
            print(uploaded_folder_path)
            if measurement_type == 'EDX':
                write_edx_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type =='MOKE':
                write_moke_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type == 'PROFIL':
                write_dektak_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type =='Smartlab':
                write_smartlab_to_hdf5(hdf5_path, uploaded_folder_path)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type == "ESRF":
                write_esrf_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type == "XRD results":
                write_xrd_results_to_hdf5(hdf5_path, uploaded_folder_path, target_dataset=dataset_name)

            return f'Failed to add measurement to {hdf5_path}.'


    @app.callback(
        [Output('hdf5_upload_folder_path', 'data'),
         Output('hdf5_measurement_type', 'value'),
         Output('hdf5_text_box', 'children', allow_duplicate=True)],
        Input('hdf5_upload', 'isCompleted'),
        State('hdf5_upload', 'fileNames'),
        State('hdf5_upload', 'upload_id'),
        State('hdf5_upload_folder_root', 'data'),
        prevent_initial_call=True
    )
    def unpack_uploaded_measurements(is_completed, uploaded_folder_path, upload_id, upload_folder_root):
        if not is_completed or not uploaded_folder_path:
            return None, None, "No file uploaded"

        uploaded_path = Path(upload_folder_root, upload_id, uploaded_folder_path[0])
        extract_dir = uploaded_path.parent / uploaded_path.stem

        if uploaded_path.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_path, 'r') as zip_file:
                filenames_list = zip_file.namelist()
                measurement_type, depth = detect_measurement(filenames_list)

                if not measurement_type:
                    output_message = f'Unable to detect measurement within {uploaded_folder_path}'
                    return None, measurement_type, output_message
                else:
                    output_message = f'{len(filenames_list)} {measurement_type} files detected in {uploaded_folder_path}'
                    zip_file.extractall(extract_dir)
                    return str(extract_dir), measurement_type, output_message


    @app.callback(
        [Output("hdf5_dataset_input", "children"),
         Output("hdf5_text_box", "children", allow_duplicate=True)],
        Input("hdf5_measurement_type", "value"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True
    )
    def switch_to_results_mode(measurement_type, hdf5_path):
        # Redefine the base children for fallback
        new_children = [
            html.Label("Dataset Name"),
            dcc.Input(
                id="hdf5_dataset_name",
                className="long_item",
                type="text",
                placeholder="Dataset Name",
                value=None
            )
        ]

        if measurement_type == "XRD results":
            with h5py.File(hdf5_path, "r") as hdf5_file:
                datasets = get_hdf5_datasets(hdf5_file, "ESRF") + get_hdf5_datasets(hdf5_file, "XRD")
            if not datasets:
                return new_children, "No ESRF or XRD datasets found in HDF5 file"
            else:
                new_children = [
                    html.Label("Dataset Name"),
                    dcc.Dropdown(
                        id="hdf5_dataset_name",
                        className="long_item",
                        options=datasets,
                        value=datasets[0],
                    )
                ]
        else:
            return new_children



