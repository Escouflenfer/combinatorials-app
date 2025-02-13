from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import re

from ..functions.functions_hdf5 import *

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
            print('ok')

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

            print(sample_dict)

            if not all(sample_dict.values()):
                return '', 'All data entries must be filled to create a new hdf5 file'

            data_path = Path(data_path)
            hdf5_path = data_path / f'{sample_name}.hdf5'
            with h5py.File(hdf5_path, "w") as file:
                file.attrs["default"] = "entry"
                file.attrs["NX_class"] = "HTroot"

                htentry = file.create_group("entry")
                htentry.attrs["NX_class"] = "HTentry"

                sample = htentry.create_group("sample")
                sample.attrs["NX_class"] = "HTsample"
                current_group = sample
                counts = 0
                for key, value in get_all_keys(sample_dict):
                    if isinstance(value, dict):
                        counts = len(value)
                        current_group = current_group.create_group(key)
                    else:
                        current_group[key] = convertFloat(value)
                        counts -= 1
                        if counts <= 0:
                            current_group = sample
                            counts = 0

            return hdf5_path, f'Created new HDF5 file at {hdf5_path}'
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


