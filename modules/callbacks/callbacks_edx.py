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
            if check_group_for_results(edx_group):
                return 'Found results for all points'
            return'No results found'
    

    # # Callback to get elements for the dropdown menu
    # @app.callback(
    #     [Output("edx_heatmap_select", "options"),
    #      Output("edx_heatmap_select", "value")],
    #     Input("edx_select_dataset", "value"),
    #     State("hdf5_path_store", "data")
    # )
    #
    # @check_conditions(edx_conditions, hdf5_path_index=1)
    # def edx_update_element_list(selected_dataset, hdf5_path):
    #     with h5py.File(hdf5_path, 'r') as hdf5_file:
    #         edx_group = hdf5_file[selected_dataset]
    #         edx_element_list = get_quantified_elements(edx_group)
    #     return edx_element_list, edx_element_list[0]
    

    # Callback for heatmap selection
    @app.callback(
        [
            Output("edx_heatmap", "figure", allow_duplicate=True),
            Output("edx_heatmap_min", "value"),
            Output("edx_heatmap_max", "value"),
            Output("edx_heatmap_select", "options"),
        ],
        Input("edx_heatmap_select", "value"),
        Input("edx_heatmap_min", "value"),
        Input("edx_heatmap_max", "value"),
        Input("edx_heatmap_precision", "value"),
        Input("edx_heatmap_edit", "value"),
        Input('hdf5_path_store', 'data'),
        Input("edx_select_dataset", "value"),
        prevent_initial_call=True,
    )
    @check_conditions(edx_conditions, hdf5_path_index=5)
    def edx_update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path, selected_dataset):
        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file[selected_dataset]

            if ctx.triggered_id in ["edx_heatmap_select", "edx_heatmap_edit", "edx_heatmap_precision"]:
                z_min = None
                z_max = None

            masking = True
            if edit_toggle in ["edit", "unfiltered"]:
                masking = False

            edx_df = edx_make_results_dataframe_from_hdf5(edx_group)
            fig = make_heatmap_from_dataframe(edx_df, values=heatmap_select, z_min=z_min, z_max=z_max,
                                              precision=precision, masking=masking)


            z_min = np.round(fig.data[0].zmin, precision)
            z_max = np.round(fig.data[0].zmax, precision)

            options = list(edx_df.columns[3:])
            if "default" in options:
                options.remove("default")

            return fig, z_min, z_max, options


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
    
    
    
    # Callback to deal with heatmap edit mode
    @app.callback(
        Output('edx_text_box', 'children', allow_duplicate=True),
        Input('edx_heatmap', 'clickData'),
        State('edx_heatmap_edit', 'value'),
        State('hdf5_path_store', 'data'),
        State('edx_select_dataset', 'value'),
        prevent_initial_call=True
    )
    @check_conditions(edx_conditions, hdf5_path_index=2)
    def heatmap_edit_mode(heatmap_click, edit_toggle, hdf5_path, selected_dataset):
        if edit_toggle != 'edit':
            raise PreventUpdate

        target_x = heatmap_click['points'][0]['x']
        target_y = heatmap_click['points'][0]['y']

        with h5py.File(hdf5_path, 'a') as hdf5_file:
            edx_group = hdf5_file[selected_dataset]
            position_group = get_target_position_group(edx_group, target_x, target_y)
            if not position_group.attrs["ignored"]:
                position_group.attrs["ignored"] = True
                return f"{target_x}, {target_y} ignore set to True"
            else:
                position_group.attrs["ignored"] = False
                return f"{target_x}, {target_y} ignore set to False"
