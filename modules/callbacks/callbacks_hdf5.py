from dash import Input, Output, State, ctx, html, dcc
from dash.exceptions import PreventUpdate
import zipfile

from ..functions.functions_edx import edx_make_results_dataframe_from_hdf5
from ..functions.functions_profil import profil_make_results_dataframe_from_hdf5
from ..functions.functions_shared import *
from ..functions.functions_xrd import xrd_make_results_dataframe_from_hdf5
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
                return f'Added {measurement_type} measurement to {hdf5_path} as {dataset_name}.'
            if measurement_type =='MOKE':
                write_moke_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path} as {dataset_name}.'
            if measurement_type == 'PROFIL':
                write_dektak_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path} as {dataset_name}.'
            if measurement_type =='XRD':
                write_smartlab_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path} as {dataset_name}.'
            if measurement_type == "ESRF":
                write_esrf_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path} as {dataset_name}.'
            if measurement_type == "XRD results":
                write_xrd_results_to_hdf5(hdf5_path, uploaded_folder_path, target_dataset=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path} as {dataset_name}.'

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
                className="long-item",
                type="text",
                placeholder="Dataset Name",
                value=None
            )
        ]

        if measurement_type == "XRD results":
            with h5py.File(hdf5_path, "r") as hdf5_file:
                datasets = get_hdf5_datasets(hdf5_file, "xrd")
            if not datasets:
                return new_children, "No ESRF or XRD datasets found in HDF5 file"
            else:
                new_children = [
                    html.Label("Dataset Name"),
                    dcc.Dropdown(
                        id="hdf5_dataset_name",
                        className="long-item",
                        options=datasets,
                        value=datasets[0],
                    )
                ]
        return new_children, ""


    @app.callback(
        Output("hdf5_text_box", "children", allow_duplicate=True),
        Input("hdf5_export", "n_clicks"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True
    )
    def export_hdf5_results_to_csv(n_clicks, hdf5_path):
        if n_clicks > 0:
            hdf5_path = Path(hdf5_path)
            general_df = None
            with h5py.File(hdf5_path, "r") as hdf5_file:
                for dataset_name, dataset_group in hdf5_file.items():
                    if dataset_name == "sample":
                        continue
                    else:
                        if dataset_group.attrs["HT_type"] == "edx":
                            df = edx_make_results_dataframe_from_hdf5(dataset_group)
                        if dataset_group.attrs["HT_type"] == "moke":
                            df = moke_make_results_dataframe_from_hdf5(dataset_group)
                        if dataset_group.attrs["HT_type"] in ["esrf","xrd"]:
                            df = xrd_make_results_dataframe_from_hdf5(dataset_group)
                        if dataset_group.attrs["HT_type"] == "profil":
                            df = profil_make_results_dataframe_from_hdf5(dataset_group)

                    df = df.drop('ignored', axis=1, errors='ignore')
                    df = df.set_index(["x_pos (mm)", "y_pos (mm)"])
                    df = df.add_suffix(f"[{dataset_name}]")
                    if general_df is None:
                        general_df = df
                    else:
                        general_df = general_df.join(df, how='outer')

            general_df.to_csv(hdf5_path.with_suffix(".csv"), index=True)

            return f"Successfully exported HDF5 to {hdf5_path.with_suffix(".csv")}"



    @app.callback(
        Output("hdf5_text_box", "children", allow_duplicate=True),
        Input("hdf5_update", "n_clicks"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True
    )
    def update_hdf5_file(n_clicks, hdf5_path):
        if n_clicks > 0:
            hdf5_path = Path(hdf5_path)
            checklist = []
            with h5py.File(hdf5_path, "a") as hdf5_file:
                for dataset_name, dataset_group in hdf5_file.items():
                    if dataset_name == "sample":
                        continue
                    if dataset_group.attrs["HT_type"] == "edx":
                        continue
                    if dataset_group.attrs["HT_type"] == "moke":
                        continue
                    if dataset_group.attrs["HT_type"] in ["esrf", "xrd"]:
                        continue
                    if dataset_group.attrs["HT_type"] == "profil":
                        update_dektak_hdf5(dataset_group)
                        checklist.append(f"[PROFIL] {dataset_name}")
            if not checklist:
                return "All datasets are already up to date"
            return f"Successfully updated datasets {checklist}"









