from dash import Input, Output, State
from pathlib import Path

from modules.functions.functions_moke import *

'''Callbacks for MOKE tab'''

def callbacks_moke(app, children_moke):

    # Callback to update profile plot based on heatmap click position
    @app.callback([Output('moke_plot', 'figure', allow_duplicate=True),
                   Output('moke_position_store', 'data')],
                  Input('moke_heatmap', 'clickData'),
                  State('moke_path_store', 'data'),
                  State('moke_plot_select', 'value'),
                  State('moke_plot_dropdown', 'value'),
                  prevent_initial_call=True
                  )
    def update_position(heatmapclick, folderpath, plot_select, measurement_id):
        folderpath = Path(folderpath)
        if heatmapclick is None:
            return go.Figure(), {}
        target_x = heatmapclick['points'][0]['x']
        target_y = heatmapclick['points'][0]['y']

        position = (target_x, target_y)

        # Plot the profile
        try:
            if plot_select == 'Loop':
                fig = loop_plot(folderpath, target_x, target_y, measurement_id)
            elif plot_select == 'Raw data':
                fig = data_plot(folderpath, target_x, target_y, measurement_id)
            else:
                fig = go.Figure()
        except NameError:
            return go.Figure(), {}

        return fig, position



    # Callback for plot selection
    @app.callback(
        Output('moke_plot', 'figure', allow_duplicate=True),
        Input('moke_plot_select', 'value'),
        Input('moke_plot_dropdown', 'value'),
        State('moke_path_store', 'data'),
        State('moke_position_store', 'data'),
        prevent_initial_call=True
    )

    def update_plot(selected_plot, measurement_id, folderpath, position):
        folderpath = Path(folderpath)
        if position is None:
            return go.Figure()
        target_x = position[0]
        target_y = position[1]
        if selected_plot == 'Loop':
            fig = loop_plot(folderpath, target_x, target_y, measurement_id)
        elif selected_plot == 'Raw data':
            fig = data_plot(folderpath, target_x, target_y, measurement_id)
        else:
            fig = go.Figure()
        return fig


    # Callback for heatmap plot selection
    @app.callback(
        Output('moke_heatmap', 'figure', allow_duplicate=True),
        Input('moke_heatmap_select', 'value'),
        Input('moke_path_store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(selected_plot, folderpath):
        folderpath = Path(folderpath)
        heatmap = heatmap_plot(folderpath, selected_plot)
        return heatmap


    # Callback to load measurements in dropdown menu
    @app.callback(
        Output('moke_plot_dropdown', 'options'),
        Output('moke_plot_dropdown', 'value'),
        Input('moke_path_store', 'data')
    )

    def update_plot_dropdown(folderpath):
        folderpath = Path(folderpath)
        number = get_measurement_number(folderpath)
        options=[{'label': 'Average', 'value': 0}]
        for n in range(number+1):
            if n != 0:
                options.append({'label': n, 'value': n})
        return options, 0
