from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import zipfile

from ..functions.functions_shared import *
from ..hdf5_compilers.hdf5compile_base import *
from ..hdf5_compilers.hdf5compile_edx import *
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
                write_edx_to_hdf5(hdf5_path, uploaded_folder_path)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type =='MOKE':
                write_moke_to_hdf5(hdf5_path, uploaded_folder_path, dataset_name=dataset_name)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type == 'PROFIL':
                write_dektak_to_hdf5(hdf5_path, uploaded_folder_path)
                return f'Added {measurement_type} measurement to {hdf5_path}.'
            if measurement_type =='XRD':
                write_xrd_to_hdf5(hdf5_path, uploaded_folder_path)
                return f'Added {measurement_type} measurement to {hdf5_path}.'

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
            return None, "No file uploaded"

        zip_path = Path(upload_folder_root, upload_id, uploaded_folder_path[0])
        extract_dir = zip_path.parent / zip_path.stem

        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            filenames_list = zip_file.namelist()
            measurement_type, depth = detect_measurement(filenames_list)

            if not measurement_type:
                output_message = f'Unable to detect measurement within {uploaded_folder_path}'
                return None, measurement_type, output_message
            else:
                output_message = f'{len(filenames_list)} {measurement_type} files detected in {uploaded_folder_path}'
                zip_file.extractall(extract_dir)
                return str(extract_dir), measurement_type, output_message



 # # Callback for unpacking uploaded measurements
    # @app.callback(
    #     [Output('hdf5_measurement_type', 'value'),
    #      Output('hdf5_measurement_store', 'data'),
    #      Output("hdf5_dataset_name", "value"),
    #      Output('hdf5_text_box', 'children', allow_duplicate=True)],
    #     Input('hdf5_upload', 'contents'),
    #     State('hdf5_upload', 'filename'),
    #     prevent_initial_call=True
    # )
    # def unpack_uploaded_measurement(contents, filename):
    #
    #     content_type, content_string = contents.split(',')
    #     decoded = base64.b64decode(content_string)
    #     zip_stream = io.BytesIO(decoded)
    #
    #     with zipfile.ZipFile(zip_stream, 'r') as zip_file:
    #         filename_list = zip_file.namelist()  # List file names in the ZIP
    #         measurement_type, depth = detect_measurement(filename_list)
    #         extracted_files = defaultdict(lambda: defaultdict(dict))
    #
    #         if measurement_type == None:
    #             output_message = f'Unable to detect measurement within {filename}'
    #             return measurement_type, {}, output_message
    #         else:
    #             filename_list = unpack_zip_directory(filename_list, depth=depth)
    #
    #         if measurement_type == 'EDX':
    #             extracted_files = {file_name: zip_file.read(file_name).decode('utf-8', errors='ignore')
    #                                for file_name in filename_list if not is_macos_system_file(file_name)}
    #         if measurement_type == 'MOKE':
    #             extracted_files = {file_name: zip_file.read(file_name).decode("iso-8859-1", errors='ignore')
    #                                for file_name in filename_list if not is_macos_system_file(file_name)}
    #         if measurement_type == 'PROFIL':
    #             extracted_files = {file_name: zip_file.read(file_name).decode("iso-8859-1", errors='ignore')
    #                                for file_name in filename_list if not is_macos_system_file(file_name)}
    #         if measurement_type == 'XRD':
    #             grouped_filenames = group_files_by_position(filename_list)
    #             print(grouped_filenames.keys())
    #             for scan_index in grouped_filenames.keys():
    #                 for file_name in grouped_filenames[scan_index]:
    #                     if file_name.endswith('.img') and not is_macos_system_file(file_name):
    #                         try:
    #                             img = fabio.open(io.BytesIO(zip_file.read(file_name)))
    #                             extracted_files[scan_index][file_name] = [img.header, img.data.tolist()]
    #                         except TypeError:
    #                             continue
    #                     elif not is_macos_system_file(file_name):
    #                         extracted_files[scan_index][file_name] = zip_file.read(file_name).decode('utf-8', errors='ignore')
    #                     else:
    #                         continue
    #
    #     output_message = f"Uploaded {len(extracted_files)} files from {filename}."
    #     dataset_name = filename.split('.')[0]
    #
    #     return measurement_type, extracted_files, dataset_name, output_message


