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
                  Input('moke_path_store', 'data')
                  )
    def load_database_path(folderpath):
        if folderpath is None:
            raise PreventUpdate

        folderpath = Path(folderpath)

        database_path = get_database_path(folderpath)
        if database_path is None:
            database_path = make_database(folderpath)

        metadata = read_metadata(database_path)

        return str(database_path), str(database_path.name), metadata



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
        State('moke_path_store', 'data'),
        State('moke_heatmap_select', 'value'),
        State('moke_heatmap_edit', 'value'),
    )

    def update_plot(selected_plot, measurement_id, position, folderpath,  heatmap_select, edit_toggle):
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

            pulse_voltage = get_pulse_voltage(folderpath) / 100
            data = load_measurement_files(folderpath, target_x, target_y, measurement_id)
            data = treat_data(data, pulse_voltage)
            data = extract_loop_from_data(data)

            if selected_plot == 'Loop':
                fig = loop_plot(data)
            elif selected_plot == 'Raw data':
                fig = data_plot(data)
            elif selected_plot == 'Loop + Derivative':
                fig = loop_derivative_plot(data)
            else:
                fig = blank_plot()

            if heatmap_select == 'Derivative Coercivity' and position is not None:
                pos, neg = calc_derivative_coercivity(data, mean=False)
                fig.add_vline(x=pos, line_width = 2, line_dash = 'dash', line_color = 'Crimson')
                fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')
            if heatmap_select == 'Measured Coercivity' and position is not None:
                pos, neg = calc_mzero_coercivity(data, mean=False)
                fig.add_vline(x=pos, line_width=2, line_dash='dash', line_color='Crimson')
                fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')

        return fig


    # Callback for heatmap plot selection
    @app.callback(
        [Output('moke_heatmap', 'figure', allow_duplicate=True),
         Output('moke_heatmap_min', 'value'),
         Output('moke_heatmap_max', 'value'),
         Output('moke_heatmap_replot_tag', 'data', allow_duplicate=True)],
        Input('moke_heatmap_select', 'value'),
        Input('moke_database_path_store', 'data'),
        Input('moke_heatmap_min', 'value'),
        Input('moke_heatmap_max', 'value'),
        Input('moke_heatmap_edit','value'),
        Input('moke_heatmap_replot_tag', 'data'),
        State('moke_path_store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(selected_plot, database_path, z_min, z_max, edit_toggle, replot_tag, folderpath):

        if database_path is None:
            return go.Figure(layout=heatmap_layout('No database found')), None, None, False

        folderpath = Path(folderpath)
        database_path = Path(database_path)

        if ctx.triggered_id in ['moke_heatmap_select', 'moke_heatmap_edit']:
            z_min = None
            z_max = None

        if ctx.triggered_id == 'moke_data_replot_tag':
            if not replot_tag:
                raise PreventUpdate

        masking = True
        if edit_toggle in ['edit', 'unfiltered']:
            masking = False

        heatmap = heatmap_plot(database_path, mode=selected_plot, title=database_path.name.strip('_database.csv'),
                               z_min=z_min, z_max=z_max, masking=masking)

        z_min = significant_round(heatmap.data[0].zmin, 3)
        z_max = significant_round(heatmap.data[0].zmax, 3)

        return heatmap, z_min, z_max, False


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
        number = get_measurement_count(folderpath)
        options=[{'label': 'Average', 'value': 0}]
        for n in range(number+1):
            if n != 0:
                options.append({'label': n, 'value': n})
        return options, 0


    # Callback to deal with heatmap edit mode
    @app.callback(
        [Output('moke_text_box', 'children', allow_duplicate=True),
         Output('moke_heatmap_replot_tag', 'data', allow_duplicate=True)],
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
        prevent_initial_call=True
    )
    def make_loop_map(n_clicks, folderpath, database_path):
        folderpath = Path(folderpath)
        database_path = Path(database_path)

        if n_clicks>0:
            figure = loop_map_plot(folderpath, database_path)
            return figure