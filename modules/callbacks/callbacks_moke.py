from dash import Input, Output, State, Dash, ctx
from dash.exceptions import PreventUpdate
from pathlib import Path

from ..functions.functions_moke import *
from ..functions.functions_shared import *

'''Callbacks for MOKE tab'''

def callbacks_moke(app, children_moke):

    @app.callback([Output('moke_database_path_store', 'data'),
                   Output('moke_path_box', 'children'),
                   Output('moke_database_metadata_store', 'data')],
                  Input('moke_make_database_button', 'n_clicks'),
                  Input('moke_path_store', 'data'),
                  State('moke_data_treatment_store', 'data'),
                  )
    def load_database_path(n_clicks, folderpath, treatment_dict):
            if folderpath is None:
                raise PreventUpdate

            folderpath = Path(folderpath)

            database_path = get_database_path(folderpath)

            if database_path is None and n_clicks == 0:
                return None, 'No database found!', None
            elif database_path is None and n_clicks > 0:
                database_path = make_database(folderpath, treatment_dict)
                metadata = read_metadata(database_path)
                return str(database_path), str(database_path.name), metadata

            elif database_path is not None:
                if compare_version(database_path) and n_clicks == 0:
                    metadata = read_metadata(database_path)
                    return str(database_path), str(database_path.name), metadata
                elif not compare_version(database_path) and n_clicks == 0:
                    return None, 'Database version incorrect, please recalculate database', None
                elif n_clicks > 0:
                    database_path = make_database(folderpath, treatment_dict)
                    metadata = read_metadata(database_path)
                    return str(database_path), str(database_path.name), metadata


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
        default_smoothing_range = 30
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


    # Callback to update profile plot based on heatmap click position
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



    # Callback for data plot
    @app.callback(
        Output('moke_plot', 'figure'),
        Input('moke_plot_select', 'value'),
        Input('moke_plot_dropdown', 'value'),
        Input('moke_position_store', 'data'),
        Input('moke_data_treatment_store', 'data'),
        State('moke_path_store', 'data'),
        State('moke_heatmap_select', 'value'),
        State('moke_heatmap_edit', 'value'),
    )

    def update_plot(selected_plot, measurement_id, position, treatment_dict, folderpath,  heatmap_select, edit_toggle):
        if folderpath is None:
            raise PreventUpdate

        if edit_toggle == 'edit':
            raise PreventUpdate

        folderpath = Path(folderpath)
        if position is None:
            fig = blank_plot()
        else:
            target_x = position[0]
            target_y = position[1]
            data = load_target_measurement_files(folderpath, target_x, target_y, measurement_id)
            data = treat_data(data, folderpath, treatment_dict)
            if selected_plot == 'Loop':
                fig = loop_plot(data)
            elif selected_plot == 'Raw data':
                fig = data_plot(data)
            elif selected_plot == 'Loop + Derivative':
                fig = loop_derivative_plot(data)
            elif selected_plot == 'Loop + Intercept':
                fig = loop_intercept_plot(data, folderpath, treatment_dict)
            else:
                fig = blank_plot()

            if heatmap_select == 'Coercivity max(dM/dH)' and position is not None:
                pos, neg = calc_derivative_coercivity(data)
                fig.add_vline(x=pos, line_width = 2, line_dash = 'dash', line_color = 'Crimson')
                fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')
            if heatmap_select == 'Coercivity M = 0' and position is not None:
                pos, neg = calc_mzero_coercivity(data)
                fig.add_vline(x=pos, line_width=2, line_dash='dash', line_color='Crimson')
                fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')

        return fig


    # Callback for heatmap plot selection
    @app.callback(
        [Output('moke_heatmap', 'figure', allow_duplicate=True),
         Output('moke_heatmap_min', 'value'),
         Output('moke_heatmap_max', 'value')],
        Input('moke_heatmap_select', 'value'),
        Input('moke_database_path_store', 'data'),
        Input('moke_heatmap_min', 'value'),
        Input('moke_heatmap_max', 'value'),
        Input('moke_heatmap_precision', 'value'),
        Input('moke_heatmap_edit','value'),
        prevent_initial_call=True
    )
    def update_heatmap(selected_plot, database_path, z_min, z_max, precision, edit_toggle):

        if database_path is None:
            return go.Figure(layout=heatmap_layout('No database found')), None, None

        database_path = Path(database_path)

        if ctx.triggered_id in ['moke_heatmap_select', 'moke_heatmap_edit']:
            z_min = None
            z_max = None

        masking = True
        if edit_toggle in ['edit', 'unfiltered']:
            masking = False

        heatmap = heatmap_plot(database_path, mode=selected_plot, title=database_path.name.strip('_database.csv'),
                               z_min=z_min, z_max=z_max, precision=precision, masking=masking)

        z_min = heatmap.data[0].zmin
        z_max = heatmap.data[0].zmax

        return heatmap, z_min, z_max


    # Callback to load measurements in dropdown menu
    @app.callback(
        Output('moke_plot_dropdown', 'options'),
        Output('moke_plot_dropdown', 'value'),
        Input('moke_path_store', 'data')
    )

    def update_plot_dropdown(folderpath):
        if folderpath is None:
            raise PreventUpdate
        folderpath = Path(folderpath)
        number = read_info_file(folderpath)['shots_per_point']
        options=[{'label': 'Average', 'value': 0}]
        for n in range(number+1):
            if n != 0:
                options.append({'label': n, 'value': n})
        return options, 0


    # Callback to deal with heatmap edit mode
    @app.callback(
        Output('moke_text_box', 'children', allow_duplicate=True),
        Input('moke_heatmap', 'clickData'),
        State('moke_heatmap_edit', 'value'),
        State('moke_database_path_store', 'data'),
        State('moke_database_metadata_store', 'data'),
        prevent_initial_call=True
    )

    def heatmap_edit_mode(clickData, edit_toggle, database_path, metadata):
        database_path = Path(database_path)

        if edit_toggle != 'edit':
            raise PreventUpdate

        target_x = clickData['points'][0]['x']
        target_y = clickData['points'][0]['y']

        database = pd.read_csv(database_path, comment='#')

        test = (database['x_pos (mm)'] == target_x) & (database['y_pos (mm)'] == target_y)
        row_number = (database[test].index[0])

        try:
            if database.loc[row_number, 'Ignore'] == 0:
                database.loc[row_number, 'Ignore'] = 1
                save_with_metadata(database, database_path, metadata)
                return f'Point x = {target_x}, y = {target_y} set to ignore', True

            else:
                database.loc[row_number, 'Ignore'] = 0
                save_with_metadata(database, database_path, metadata)
                return f'Point x = {target_x}, y = {target_y} no longer ignored', True

        except KeyError:
            return 'Invalid database. Please delete and reload to make a new one', False



    @app.callback(
        Output('moke_loop_map_figure', 'figure'),
        Input('moke_loop_map_button', 'n_clicks'),
        State('moke_path_store', 'data'),
        State('moke_database_path_store', 'data'),
        State('moke_data_treatment_store', 'data'),
        State('moke_loop_map_checklist', 'value'),
        prevent_initial_call=True
    )
    def make_loop_map(n_clicks, folderpath, database_path, treatment_dict, checklist):
        folderpath = Path(folderpath)
        database_path = Path(database_path)

        normalize = False
        if "normalize" in checklist:
            normalize = True

        if n_clicks>0:
            figure = loop_map_plot(folderpath, database_path, treatment_dict, normalize)
            return figure


    # Callback to save heatmap
    @app.callback(
        Output('moke_text_box', 'children', allow_duplicate=True),
        Input('moke_heatmap_save','n_clicks'),
        State('moke_heatmap', 'figure'),
        State('moke_path_store', 'data'),
        prevent_initial_call=True
        )

    def save_heatmap(n_clicks, heatmap_fig, folderpath):
        if folderpath is None:
            raise PreventUpdate
        folderpath = Path(folderpath)
        heatmap_fig = go.Figure(heatmap_fig)
        if n_clicks>0:
            heatmap_fig.update_layout(
                titlefont=dict(size=30),
                xaxis=dict(title='X (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
                yaxis=dict(title='Y (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
                height=700,
                width=700
            )

            heatmap_fig.update_traces(
                colorbar=dict(
                    tickfont=dict(size=20),
                    titlefont=dict(size=25),
                    thickness=20
                )
            )

            # heatmap_fig.write_image(folderpath / heatmap_fig.layout.title.text, format="pdf")
            heatmap_fig.write_image(folderpath / 'heatmap.png', format="png")

            return f'Saved heatmap to png at {folderpath}'


    # Callback to save plot
    @app.callback(
        Output('moke_text_box', 'children', allow_duplicate=True),
        Input('moke_plot_save', 'n_clicks'),
        State('moke_plot', 'figure'),
        State('moke_path_store', 'data'),
        prevent_initial_call=True
    )
    def save_plot(n_clicks, plot_fig, folderpath):
        if folderpath is None:
            raise PreventUpdate
        folderpath = Path(folderpath)
        plot_fig = go.Figure(plot_fig)
        if n_clicks > 0:
            plot_fig.update_layout(
                titlefont=dict(size=30),
                xaxis=dict(tickfont=dict(size=20), titlefont=dict(size=25)),
                yaxis=dict(tickfont=dict(size=20), titlefont=dict(size=25)),
                height=700,
                width=1100
            )


            # heatmap_fig.write_image(folderpath / heatmap_fig.layout.title.text, format="pdf")
            plot_fig.write_image(folderpath / 'plot.png', format="png")

            return f'Saved plot to png at {folderpath}'