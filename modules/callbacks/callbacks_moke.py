from dash import Input, Output, State, Dash, ctx
from dash.exceptions import PreventUpdate
from pathlib import Path

from ..functions.functions_moke import *
from ..functions.functions_shared import *

'''Callbacks for MOKE tab'''

def callbacks_moke(app, children_moke):

    # Callback to update moke plot based on heatmap click position
    @app.callback(Output('moke_position_store', 'data'),
                  Input('moke_heatmap', 'clickData'),
                  prevent_initial_call=True
                  )
    def update_position(clickData):
        if clickData is None:
            return None
        target_x = clickData['points'][0]['x']
        target_y = clickData['points'][0]['y']

        position = (target_x, target_y)

        return position



    # Callback to check if HDF5 has results
    @app.callback(
        Output("moke_text_box", "children", allow_duplicate=True),
        Input("hdf5_path_store", "data"),
        prevent_initial_call=True,
    )
    def moke_check_for_results(hdf5_path):
        if check_hdf5_for_results(hdf5_path, 'moke', mode='all'):
            return 'Found results for all points'
        elif check_hdf5_for_results(hdf5_path, 'moke', mode='any'):
            return 'Found results for some points'
        else:
            return'No results found'


    # Callback for heatmap selection
    @app.callback(
        [
            Output("moke_heatmap", "figure", allow_duplicate=True),
            Output("moke_heatmap_min", "value"),
            Output("moke_heatmap_max", "value"),
        ],
        Input("moke_heatmap_select", "value"),
        Input("moke_heatmap_min", "value"),
        Input("moke_heatmap_max", "value"),
        Input("moke_heatmap_precision", "value"),
        Input("moke_heatmap_edit", "value"),
        Input('hdf5_path_store', 'data'),
        prevent_initial_call=True,
    )
    def moke_update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path):
        hdf5_path = Path(hdf5_path)
        if hdf5_path is None:
            raise PreventUpdate

        with h5py.File(hdf5_path, 'r') as hdf5_file:

            if ctx.triggered_id in ["moke_heatmap_select", "moke_heatmap_edit", "moke_heatmap_precision"]:
                z_min = None
                z_max = None

            masking = True
            if edit_toggle in ["edit", "unfiltered"]:
                masking = False

            moke_df = moke_make_results_dataframe_from_hdf5(hdf5_file)
            fig = make_heatmap_from_dataframe(moke_df, values=heatmap_select, z_min=z_min, z_max=z_max, precision=precision)

            z_min = np.round(fig.data[0].zmin, precision)
            z_max = np.round(fig.data[0].zmax, precision)

            return fig, z_min, z_max


    # Profile plot
    @app.callback(
        Output("moke_plot", "figure"),
        Input("hdf5_path_store", "data"),
        Input("moke_position_store", "data"),
        Input("moke_plot_select", "value"),
        Input("moke_data_treatment_store", "data"),
        Input("moke_heatmap_select", "value"),
    )
    def moke_update_plot(hdf5_path, position, plot_options, treatment_dict, heatmap_select):
        if hdf5_path is None or position is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        hdf5_path = Path(hdf5_path)

        fig = go.Figure()

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            measurement_df = moke_get_measurement_from_hdf5(hdf5_file, target_x, target_y)
            results_dict = moke_get_results_from_hdf5(hdf5_file, target_x, target_y)

        measurement_df = moke_treat_measurement_dataframe(measurement_df, treatment_dict)

        if plot_options == "oscilloscope":
            fig = moke_plot_oscilloscope_from_dataframe(fig, measurement_df)
        elif plot_options == "loop":
            fig = moke_plot_loop_from_dataframe(fig, measurement_df)
        elif plot_options == "stored_result":
            fig = moke_plot_loop_from_dataframe(fig, measurement_df)
            if heatmap_select == "coercivity_m0_(T)":
                moke_plot_vlines(fig, values=[results_dict["coercivity_m0"]["negative"],
                                              results_dict["coercivity_m0"]["positive"]])
            if heatmap_select == "coercivity_dmdh_(T)":
                moke_plot_vlines(fig, values=[results_dict["coercivity_dmdh"]["negative"],
                                              results_dict["coercivity_dmdh"]["positive"]])
            if heatmap_select == "intercept_field_(T)":
                moke_plot_vlines(fig, values=[results_dict["coercivity_dmdh"]["negative"],
                                              results_dict["coercivity_dmdh"]["positive"]])

        fig.update_layout(plot_layout(title=''))

        return fig


    @app.callback(
        Output("moke_text_box", "children", allow_duplicate=True),
        Input("moke_make_database_button", "n_clicks"),
        State("hdf5_path_store", "data"),
        State("moke_data_treatment_store", "data"),
        prevent_initial_call=True,
    )
    def moke_make_database(n_clicks, hdf5_path, treatment_dict):
        if hdf5_path is None:
            raise PreventUpdate

        hdf5_path = Path(hdf5_path)
        if n_clicks > 0:
            with h5py.File(hdf5_path, 'a') as hdf5_file:
                results_dict = moke_batch_fit(hdf5_file, treatment_dict)
                moke_results_dict_to_hdf5(hdf5_file, results_dict, treatment_dict)
                return "Great Success!"


    @app.callback([Output('moke_data_treatment_store', 'data'),
                   Output('moke_coil_factor', 'value'),
                   Output('moke_smoothing_polyorder', 'value'),
                   Output('moke_smoothing_range', 'value')],
                  Input('moke_data_treatment_checklist', 'value'),
                  Input('moke_coil_factor', 'value'),
                  Input('moke_smoothing_polyorder', 'value'),
                  Input('moke_smoothing_range', 'value'),
                  Input('moke_database_path_store', 'data'),
                  State('moke_database_metadata_store', 'data'),
                  )

    def store_data_treatment(treatment_checklist, coil_factor, smoothing_polyorder,
                             smoothing_range, database_path, metadata):
        default_coil_factor = 0.92667
        default_smoothing_polyorder = 1
        default_smoothing_range = 10
        if database_path is not None:
            if metadata is None:
                metadata = read_metadata(database_path)
            if coil_factor is None:
                try:
                    coil_factor = metadata['coil_factor']
                except TypeError or KeyError:
                    pass
            if smoothing_polyorder is None:
                try:
                    smoothing_polyorder = metadata['smoothing_polyorder']
                except TypeError or KeyError:
                    pass
            if smoothing_range is None:
                try:
                    smoothing_range = metadata['smoothing_range']
                except TypeError or KeyError:
                    pass
        else:
            if coil_factor is None:
                coil_factor = default_coil_factor
            if smoothing_polyorder is None:
                smoothing_polyorder = default_smoothing_polyorder
            if smoothing_range is None:
                smoothing_range = default_smoothing_range


        treatment_dict = {"coil_factor" : coil_factor,
                          "smoothing": False,
                          "smoothing_polyorder": smoothing_polyorder,
                          "smoothing_range": smoothing_range,
                          "correct_offset": False,
                          "filter_zero": False,
                          "connect_loops": False,
                          "pulse_voltage": 432
        }

        if "smoothing" in treatment_checklist:
            treatment_dict.update({"smoothing": True})
        if "correct_offset" in treatment_checklist:
            treatment_dict.update({"correct_offset": True})
        if "filter_zero" in treatment_checklist:
            treatment_dict.update({"filter_zero": True})
        if "connect_loops" in treatment_checklist:
            treatment_dict.update({"connect_loops": True})


        return treatment_dict, coil_factor, smoothing_polyorder, smoothing_range
    #
    #
    #
    #
    #
    # # Callback for data plot
    # @app.callback(
    #     Output('moke_plot', 'figure'),
    #     Input('moke_plot_select', 'value'),
    #     Input('moke_plot_dropdown', 'value'),
    #     Input('moke_position_store', 'data'),
    #     Input('moke_data_treatment_store', 'data'),
    #     State('moke_path_store', 'data'),
    #     State('moke_heatmap_select', 'value'),
    #     State('moke_heatmap_edit', 'value'),
    # )
    #
    # def update_plot(selected_plot, measurement_id, position, treatment_dict, folderpath,  heatmap_select, edit_toggle):
    #     if folderpath is None:
    #         raise PreventUpdate
    #
    #     if edit_toggle == 'edit':
    #         raise PreventUpdate
    #
    #     folderpath = Path(folderpath)
    #     if position is None:
    #         fig = blank_plot()
    #     else:
    #         target_x = position[0]
    #         target_y = position[1]
    #         data = load_target_measurement_files(folderpath, target_x, target_y, measurement_id)
    #         data = treat_data(data, folderpath, treatment_dict)
    #         if selected_plot == 'Loop':
    #             fig = loop_plot(data)
    #         elif selected_plot == 'Raw data':
    #             fig = data_plot(data)
    #         elif selected_plot == 'Loop + Derivative':
    #             fig = loop_derivative_plot(data)
    #         elif selected_plot == 'Loop + Intercept':
    #             fig = loop_intercept_plot(data, folderpath, treatment_dict)
    #         else:
    #             fig = blank_plot()
    #
    #         if heatmap_select == 'Coercivity max(dM/dH)' and position is not None:
    #             pos, neg = calc_derivative_coercivity(data)
    #             fig.add_vline(x=pos, line_width = 2, line_dash = 'dash', line_color = 'Crimson')
    #             fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')
    #         if heatmap_select == 'Coercivity M = 0' and position is not None:
    #             pos, neg = calc_mzero_coercivity(data)
    #             fig.add_vline(x=pos, line_width=2, line_dash='dash', line_color='Crimson')
    #             fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')
    #
    #     return fig
    #
    #
    # # Callback for heatmap plot selection
    # @app.callback(
    #     [Output('moke_heatmap', 'figure', allow_duplicate=True),
    #      Output('moke_heatmap_min', 'value'),
    #      Output('moke_heatmap_max', 'value')],
    #     Input('moke_heatmap_select', 'value'),
    #     Input('moke_database_path_store', 'data'),
    #     Input('moke_heatmap_min', 'value'),
    #     Input('moke_heatmap_max', 'value'),
    #     Input('moke_heatmap_edit','value'),
    #     prevent_initial_call=True
    # )
    # def update_heatmap(selected_plot, database_path, z_min, z_max, edit_toggle):
    #
    #     if database_path is None:
    #         return go.Figure(layout=heatmap_layout('No database found')), None, None
    #
    #     database_path = Path(database_path)
    #
    #     if ctx.triggered_id in ['moke_heatmap_select', 'moke_heatmap_edit']:
    #         z_min = None
    #         z_max = None
    #
    #     masking = True
    #     if edit_toggle in ['edit', 'unfiltered']:
    #         masking = False
    #
    #     heatmap = heatmap_plot(database_path, mode=selected_plot, title=database_path.name.strip('_database.csv'),
    #                            z_min=z_min, z_max=z_max, masking=masking)
    #
    #     z_min = significant_round(heatmap.data[0].zmin, 3)
    #     z_max = significant_round(heatmap.data[0].zmax, 3)
    #
    #     return heatmap, z_min, z_max
    #
    #
    # # Callback to load measurements in dropdown menu
    # @app.callback(
    #     Output('moke_plot_dropdown', 'options'),
    #     Output('moke_plot_dropdown', 'value'),
    #     Input('moke_path_store', 'data')
    # )
    #
    # def update_plot_dropdown(folderpath):
    #     if folderpath is None:
    #         raise PreventUpdate
    #     folderpath = Path(folderpath)
    #     number = read_info_file(folderpath)['shots_per_point']
    #     options=[{'label': 'Average', 'value': 0}]
    #     for n in range(number+1):
    #         if n != 0:
    #             options.append({'label': n, 'value': n})
    #     return options, 0
    #
    #
    # # Callback to deal with heatmap edit mode
    # @app.callback(
    #     Output('moke_text_box', 'children', allow_duplicate=True),
    #     Input('moke_heatmap', 'clickData'),
    #     State('moke_heatmap_edit', 'value'),
    #     State('moke_database_path_store', 'data'),
    #     State('moke_database_metadata_store', 'data'),
    #     prevent_initial_call=True
    # )
    #
    # def heatmap_edit_mode(clickData, edit_toggle, database_path, metadata):
    #     database_path = Path(database_path)
    #
    #     if edit_toggle != 'edit':
    #         raise PreventUpdate
    #
    #     target_x = clickData['points'][0]['x']
    #     target_y = clickData['points'][0]['y']
    #
    #     database = pd.read_csv(database_path, comment='#')
    #
    #     test = (database['x_pos (mm)'] == target_x) & (database['y_pos (mm)'] == target_y)
    #     row_number = (database[test].index[0])
    #
    #     try:
    #         if database.loc[row_number, 'Ignore'] == 0:
    #             database.loc[row_number, 'Ignore'] = 1
    #             save_with_metadata(database, database_path, metadata)
    #             return f'Point x = {target_x}, y = {target_y} set to ignore', True
    #
    #         else:
    #             database.loc[row_number, 'Ignore'] = 0
    #             save_with_metadata(database, database_path, metadata)
    #             return f'Point x = {target_x}, y = {target_y} no longer ignored', True
    #
    #     except KeyError:
    #         return 'Invalid database. Please delete and reload to make a new one', False
    #
    #
    #
    # @app.callback(
    #     Output('moke_loop_map_figure', 'figure'),
    #     Input('moke_loop_map_button', 'n_clicks'),
    #     State('moke_path_store', 'data'),
    #     State('moke_database_path_store', 'data'),
    #     State('moke_data_treatment_store', 'data'),
    #     State('moke_loop_map_checklist', 'value'),
    #     prevent_initial_call=True
    # )
    # def make_loop_map(n_clicks, folderpath, database_path, treatment_dict, checklist):
    #     folderpath = Path(folderpath)
    #     database_path = Path(database_path)
    #
    #     normalize = False
    #     if "normalize" in checklist:
    #         normalize = True
    #
    #     if n_clicks>0:
    #         figure = loop_map_plot(folderpath, database_path, treatment_dict, normalize)
    #         return figure
    #