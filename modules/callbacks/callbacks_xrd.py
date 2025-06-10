"""

"""
from array import array

from dash import Input, Output, callback
from dash.exceptions import PreventUpdate
from ..functions.functions_xrd import *
from ..functions.functions_shared import *


def callbacks_xrd(app, children_xrd):
    
    # Callback to update current position
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

            
    # Callback for heatmap selection
    @app.callback(
        [
            Output("xrd_heatmap", "figure", allow_duplicate=True),
            Output("xrd_heatmap_min", "value"),
            Output("xrd_heatmap_max", "value"),
            Output("xrd_heatmap_select", "options"),
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
            fig = make_heatmap_from_dataframe(xrd_df, values=heatmap_select, z_min=z_min, z_max=z_max,
                                              precision=precision, masking=masking)

            z_min = np.round(fig.data[0].zmin, precision)
            z_max = np.round(fig.data[0].zmax, precision)

            options = list(xrd_df.columns[3:])
            if "default" in options:
                options.remove("default")

            return fig, z_min, z_max, options



    @app.callback(
        [
            Output("xrd_plot", "figure"),
            Output("xrd_fits_select", "options"),
            Output("xrd_fits_select", "value"),
            Output("xrd_image_min", "value"),
            Output("xrd_image_max", "value"),
        ],
        Input("xrd_position_store", "data"),
        Input("xrd_plot_select", "value"),
        Input("xrd_select_dataset", "value"),
        Input("xrd_fits_select", "value"),
        Input("xrd_image_min", "value"),
        Input("xrd_image_max", "value"),
        Input("hdf5_path_store", "data"),
    )
    @check_conditions(xrd_conditions, hdf5_path_index=6)
    def xrd_update_plot(position, plot_select, selected_dataset, fits_select, z_min, z_max, hdf5_path):
        if position is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        options = []

        fig = go.Figure()

        if not plot_select == "image":
            z_min = None
            z_max = None

        with h5py.File(hdf5_path, "r") as hdf5_file:
            xrd_group = hdf5_file[selected_dataset]
            if plot_select == "integrated":
                measurement_df = xrd_get_integrated_from_hdf5(xrd_group, target_x, target_y)
                fig = xrd_plot_integrated_from_dataframe(fig, measurement_df)
                fig.update_layout(plot_layout(title=""))

            if plot_select == "fitted":
                fits_df = xrd_get_fits_from_hdf5(xrd_group, target_x, target_y)
                options = fits_df.columns[1:]
                fig = xrd_plot_fits_from_dataframe(fig, fits_df, fits_select)
                fig.update_layout(plot_layout(title="", showlegend=True))

            if plot_select == "image":
                image_array = xrd_get_image_from_hdf5(xrd_group, target_x, target_y)
                fig = xrd_plot_image_from_array(image_array, z_min, z_max)
                z_min = np.round(fig.data[0].zmin, 0)
                z_max = np.round(fig.data[0].zmax, 0)


        # Prevent resetting of xrd_fits_select
        if ctx.triggered_id in ["xrd_fits_select"]:
            fits_select_value = fits_select
        else:
            fits_select_value = options




        return fig, options, fits_select_value, z_min, z_max
        

    # Callback to deal with heatmap edit mode
    @app.callback(
        Output('xrd_text_box', 'children', allow_duplicate=True),
        Input('xrd_heatmap', 'clickData'),
        State('xrd_heatmap_edit', 'value'),
        State('hdf5_path_store', 'data'),
        State('xrd_select_dataset', 'value'),
        prevent_initial_call=True
    )
    @check_conditions(xrd_conditions, hdf5_path_index=2)
    def heatmap_edit_mode(heatmap_click, edit_toggle, hdf5_path, selected_dataset):
        if edit_toggle != 'edit':
            raise PreventUpdate

        target_x = heatmap_click['points'][0]['x']
        target_y = heatmap_click['points'][0]['y']

        with h5py.File(hdf5_path, 'a') as hdf5_file:
            xrd_group = hdf5_file[selected_dataset]
            position_group = get_target_position_group(xrd_group, target_x, target_y)
            if not position_group.attrs["ignored"]:
                position_group.attrs["ignored"] = True
                return f"{target_x}, {target_y} ignore set to True"
            else:
                position_group.attrs["ignored"] = False
                return f"{target_x}, {target_y} ignore set to False"
