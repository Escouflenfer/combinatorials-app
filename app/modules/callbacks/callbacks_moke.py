from dash import Input, Output, State
from pathlib import Path

from ..functions.functions_moke import *

'''Callbacks for MOKE tab'''

def callbacks_moke(app, children_moke):
    # Callback to update profile plot based on heatmap click position
    @app.callback(Output('moke_position_store', 'data'),
                  Input('moke_heatmap', 'clickData'),
                  prevent_initial_call=True
                  )
    def update_position(heatmapclick):
        if heatmapclick is None:
            return None
        target_x = heatmapclick['points'][0]['x']
        target_y = heatmapclick['points'][0]['y']

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
    )

    def update_plot(selected_plot, measurement_id, position, folderpath,  heatmap_select):
        folderpath = Path(folderpath)
        if position is None:
            fig = blank_plot()
        else:
            target_x = position[0]
            target_y = position[1]
            if selected_plot == 'Loop':
                fig = loop_plot(folderpath, target_x, target_y, measurement_id)
            elif selected_plot == 'Raw data':
                fig = data_plot(folderpath, target_x, target_y, measurement_id)
            elif selected_plot == 'Loop + Derivative':
                fig = loop_derivative_plot(folderpath, target_x, target_y, measurement_id)
            else:
                fig = blank_plot()

            if heatmap_select == 'Derivative Coercivity' and position is not None:
                pos, neg = get_derivative_coercivity(folderpath, target_x, target_y, mean=False)
                fig.add_vline(x=pos, line_width = 2, line_dash = 'dash', line_color = 'Crimson')
                fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')
            if heatmap_select == 'Measured Coercivity' and position is not None:
                pos, neg = get_measured_coercivity(folderpath, target_x, target_y, mean=False)
                fig.add_vline(x=pos, line_width=2, line_dash='dash', line_color='Crimson')
                fig.add_vline(x=neg, line_width=2, line_dash='dash', line_color='Crimson')

        return fig


    # Callback for heatmap plot selection
    @app.callback(
        [Output('moke_heatmap', 'figure', allow_duplicate=True),
         Output('moke_text_box', 'children', allow_duplicate=True)],
        Input('moke_heatmap_select', 'value'),
        Input('moke_path_store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(selected_plot, folderpath):
        folderpath = Path(folderpath)
        for file in folderpath.glob('*.csv'):
            database_path = file
        if not any(folderpath.glob('*.csv')):
            database_path = make_database(folderpath)
        heatmap = heatmap_plot(folderpath, selected_plot)
        return heatmap, str(database_path)


    # Callback to load measurements in dropdown menu
    @app.callback(
        Output('moke_plot_dropdown', 'options'),
        Output('moke_plot_dropdown', 'value'),
        Input('moke_path_store', 'data')
    )

    def update_plot_dropdown(folderpath):
        folderpath = Path(folderpath)
        number = get_measurement_count(folderpath)
        options=[{'label': 'Average', 'value': 0}]
        for n in range(number+1):
            if n != 0:
                options.append({'label': n, 'value': n})
        return options, 0


    # Callback to save heatmap
    @app.callback(
        Output('moke_text_box', 'children', allow_duplicate=True),
        Input('moke_heatmap_save','n_clicks'),
        State('moke_heatmap', 'figure'),
        State('moke_path_store', 'data'),
        prevent_initial_call=True
        )

    def save_heatmap(n_clicks, heatmap_fig, folderpath):
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