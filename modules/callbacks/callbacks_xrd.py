"""

"""

from dash import Input, Output, callback
from dash.exceptions import PreventUpdate
from ..functions.functions_xrd import *
from ..functions.functions_shared import *


def callbacks_xrd(app, children_xrd):
    
    # Callback to update xrd plot based on heatmap click position
    @app.callback(Output('xrd_position_store', 'data'),
                  Input('xrd_heatmap', 'clickData'),
                  prevent_initial_call=True
                  )
    def update_position(heatmap_click):
        if heatmap_click is None:
            return None
        target_x = heatmap_click['points'][0]['x']
        target_y = heatmap_click['points'][0]['y']

        position = (target_x, target_y)

        return position

    @app.callback(
        [Output("xrd_select_dataset", "options"),
         Output("xrd_select_dataset", "value")],
        Input("hdf5_path_store", "data"),
    )
    @check_conditions(xrd_conditions, hdf5_path_index=0)
    def xrd_scan_hdf5_for_datasets(hdf5_path):
        with h5py.File(hdf5_path, "r") as hdf5_file:
            dataset_list = get_hdf5_datasets(hdf5_file, dataset_type='xrd')

        return dataset_list, dataset_list[0]


    # Callback to check if HDF5 has results
    @app.callback(
        [Output("xrd_heatmap_select", "options"),
         Output("xrd_heatmap_select", "value"),
        Output("xrd_text_box", "children", allow_duplicate=True)],
        Input("xrd_select_dataset", "value"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True,
    )
    @check_conditions(xrd_conditions, hdf5_path_index=1)
    def xrd_check_for_results(selected_dataset, hdf5_path):
        if selected_dataset is None:
            raise PreventUpdate

        with h5py.File(hdf5_path, "r") as hdf5_file:
            xrd_group = hdf5_file[selected_dataset]
            if check_group_for_results(xrd_group):
                results_key_list = {}
                for position, position_group in xrd_group.items():
                    results_group = position_group['results']
                return 'Found results for all points'
            else:
                return 'Missing results'

            
    # Callback for heatmap selection
    @app.callback(
        [
            Output("xrd_heatmap", "figure", allow_duplicate=True),
            Output("xrd_heatmap_min", "value"),
            Output("xrd_heatmap_max", "value"),
        ],
        Input("xrd_heatmap_select", "value"),
        Input("xrd_heatmap_min", "value"),
        Input("xrd_heatmap_max", "value"),
        Input("xrd_heatmap_precision", "value"),
        Input("xrd_heatmap_edit", "value"),
        Input('hdf5_path_store', 'data'),
        Input("xrd_select_dataset", "value"),
        prevent_initial_call=True,
    )
    @check_conditions(xrd_conditions, hdf5_path_index=5)
    def xrd_update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path, selected_dataset):
        with h5py.File(hdf5_path, 'r') as hdf5_file:
            xrd_group = hdf5_file[selected_dataset]

            if ctx.triggered_id in ["xrd_heatmap_select", "xrd_heatmap_edit", "xrd_heatmap_precision"]:
                z_min = None
                z_max = None

            masking = True
            if edit_toggle in ["edit", "unfiltered"]:
                masking = False

            xrd_df = xrd_make_results_dataframe_from_hdf5(xrd_group)
            fig = make_heatmap_from_dataframe(xrd_df, values=heatmap_select, z_min=z_min, z_max=z_max, precision=precision)

            z_min = np.round(fig.data[0].zmin, precision)
            z_max = np.round(fig.data[0].zmax, precision)

            return fig, z_min, z_max