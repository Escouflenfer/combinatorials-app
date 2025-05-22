from ..functions.functions_edx import *

def callbacks_edx(app):

    # Callback to update position based on heatmap click
    @app.callback(Output('edx_position_store', 'data'),
                  Input('edx_heatmap', 'clickData'),
                  prevent_initial_call=True
                  )
    def edx_update_position(heatmap_click):
        if heatmap_click is None:
            return None
        target_x = heatmap_click['points'][0]['x']
        target_y = heatmap_click['points'][0]['y']

        position = (target_x, target_y)

        return position


    # Callback to find all relevant datasets in HDF5 file
    @app.callback(
        [Output("edx_select_dataset", "options"),
         Output("edx_select_dataset", "value")],
        Input("hdf5_path_store", "data"),
    )
    @check_conditions(edx_conditions, hdf5_path_index=0)
    def edx_scan_hdf5_for_datasets(hdf5_path):
        with h5py.File(hdf5_path, "r") as hdf5_file:
            dataset_list = get_hdf5_datasets(hdf5_file, dataset_type='edx')

        return dataset_list, dataset_list[0]
    
    
    # Callback to check if HDF5 has results
    @app.callback(
        Output("edx_text_box", "children", allow_duplicate=True),
        Input("edx_select_dataset", "value"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True,
    )
    @check_conditions(edx_conditions, hdf5_path_index=1)
    def edx_check_for_results(selected_dataset, hdf5_path):
        if selected_dataset is None:
            raise PreventUpdate

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file[selected_dataset]
            if check_group_for_results(edx_group, mode='all'):
                return 'Found results for all points'
            elif check_group_for_results(edx_group, mode='any'):
                return 'Found results for some points'
            else:
                return'No results found'
    

    # Callback to get elements for the dropdown menu
    @app.callback(
        [Output("edx_heatmap_select", "options"),
         Output("edx_heatmap_select", "value")],
        Input("edx_select_dataset", "value"),
        State("hdf5_path_store", "data")
    )

    @check_conditions(edx_conditions, hdf5_path_index=1)
    def edx_update_element_list(selected_dataset, hdf5_path):
        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file[selected_dataset]
            edx_element_list = get_quantified_elements(edx_group)
        return edx_element_list, edx_element_list[0]
    

    # Callback to plot EDX heatmap
    @app.callback(
        [Output("edx_heatmap", "figure"),
         Output('edx_heatmap_min', 'value'),
         Output('edx_heatmap_max', 'value')],
        Input("edx_heatmap_select", "value"),
        Input('edx_heatmap_min', 'value'),
        Input('edx_heatmap_max', 'value'),
        Input('edx_heatmap_precision', 'value'),
        Input("edx_select_dataset", "value"),
        State("hdf5_path_store", "data"),
    )
    @check_conditions(edx_conditions, hdf5_path_index=5)
    def edx_update_heatmap(heatmap_select, z_min, z_max, precision, selected_dataset, hdf5_path):
        if ctx.triggered_id in ['edx_heatmap_select', 'edx_heatmap_precision'] :
            z_min = None
            z_max = None

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file[selected_dataset]
            edx_df = edx_make_results_dataframe_from_hdf5(edx_group)

        fig = make_heatmap_from_dataframe(edx_df, values=heatmap_select, z_min=z_min, z_max=z_max, precision=precision)

        z_min = np.round(fig.data[0].zmin, precision)
        z_max = np.round(fig.data[0].zmax, precision)

        # Update the dimensions of the heatmap and the X-Y title axes
        # sample_name = folderpath.parent.name
        # layout=heatmap_layout('EDX Composition Map <br>' + sample_name)
        # fig.update_layout(layout)

        return fig, z_min, z_max


    # EDX plot
    @app.callback(
        Output("edx_plot", "figure"),
        Input("edx_select_dataset", "value"),
        Input("edx_position_store", "data"),
        State("hdf5_path_store", "data"),
    )
    @check_conditions(edx_conditions, hdf5_path_index=2)
    def edx_update_plot(selected_dataset, position, hdf5_path):
        if position is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file[selected_dataset]
            measurement_df = edx_get_measurement_from_hdf5(edx_group, target_x, target_y)

        fig = edx_plot_measurement_from_dataframe(measurement_df)

        return fig
