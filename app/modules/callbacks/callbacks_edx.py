from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from ..functions.functions_edx import *

def callbacks_edx(app):

    # Callback to update position based on heatmap click
    @app.callback(Output('edx_position_store', 'data'),
                  Input('edx_heatmap', 'clickData'),
                  prevent_initial_call=True
                  )
    def update_position(heatmapclick):
        if heatmapclick is None:
            return None
        target_x = heatmapclick['points'][0]['x']
        target_y = heatmapclick['points'][0]['y']

        position = (target_x, target_y)

        return position


    # Callback to get elements for the dropdown menu
    @app.callback(Output("element_edx", "options"),
                  Input("edx_path_store", "data"))
    def update_element_edx(folderpath):
        if folderpath is None:
            raise PreventUpdate
        element_edx_opt = get_elements(folderpath)
        return element_edx_opt

    # Callback to plot EDX heatmap
    @app.callback(
        Output("edx_heatmap", "figure"),
        Input("element_edx", "value"),
        Input('edx_heatmap_min', 'value'),
        Input('edx_heatmap_max', 'value'),
        State("edx_path_store", "data"),
    )
    def update_heatmap_edx(element_edx, z_min, z_max, folderpath):
        if folderpath is None:
            raise PreventUpdate
        fig = generate_heatmap(folderpath, element_edx, z_min, z_max)

        # Update the dimensions of the heatmap and the X-Y title axes
        fig.update_layout(height=750, width=750, clickmode="event+select")
        fig.update_xaxes(title="X Position")
        fig.update_yaxes(title="Y Position")

        return fig

    #   EDX spectra
    @app.callback(
        Output("edx_spectra", "figure"),
        Input("edx_path_store", "data"),
        Input("edx_position_store", "data"),
        Input("xrange_slider", "value"),
        Input("yrange_slider", "value"),
    )
    def update_spectra(folderpath, position, xrange, yrange):
        folderpath = Path(folderpath)
        if folderpath is None:
            raise PreventUpdate
        if position is None:
            raise PreventUpdate
        else:
            target_x = position[0]
            target_y = position[1]

        fig, meta = generate_spectra(folderpath, target_x, target_y)
        fig.update_layout(
            title=f"EDX Spectrum for {folderpath} at position ({target_x}, {target_y})",
            height=750,
            width=1100,
            annotations=[meta],
        )
        fig.update_xaxes(title="Energy (keV)", range=xrange)
        fig.update_yaxes(title="Counts", range=yrange)
        return fig


    # # Callback to save heatmap
    # @app.callback(
    #     Output('dektak_text_box', 'children', allow_duplicate=True),
    #     Input('dektak_heatmap_save', 'n_clicks'),
    #     State('dektak_heatmap', 'figure'),
    #     State('dektak_path_store', 'data'),
    #     prevent_initial_call=True
    # )
    # def save_heatmap_to_pdf(n_clicks, heatmap_fig, folderpath):
    #     folderpath = Path(folderpath)
    #     heatmap_fig = go.Figure(heatmap_fig)
    #     if n_clicks > 0:
    #         heatmap_fig.update_layout(
    #             titlefont=dict(size=30),
    #             xaxis=dict(title='X (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
    #             yaxis=dict(title='Y (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
    #             height=700,
    #             width=700
    #         )
    #
    #         heatmap_fig.update_traces(
    #             colorbar=dict(
    #                 tickfont=dict(size=20),
    #                 titlefont=dict(size=25),
    #                 thickness=20
    #             )
    #         )
    #
    #         # heatmap_fig.write_image(folderpath / heatmap_fig.layout.title.text, format="pdf")
    #         heatmap_fig.write_image(folderpath / 'heatmap.png', format="png")
    #
    #         return f'Saved heatmap to png at {folderpath}'
    #
    #     # Callback to save plot
    #     @app.callback(
    #         Output('dektak_text_box', 'children', allow_duplicate=True),
    #         Input('dektak_plot_save', 'n_clicks'),
    #         State('dektak_plot', 'figure'),
    #         State('dektak_path_store', 'data'),
    #         prevent_initial_call=True
    #     )
    #     def save_plot(n_clicks, plot_fig, folderpath):
    #         folderpath = Path(folderpath)
    #         plot_fig = go.Figure(plot_fig)
    #         if n_clicks > 0:
    #             plot_fig.update_layout(
    #                 titlefont=dict(size=30),
    #                 xaxis=dict(title='X (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
    #                 yaxis=dict(title='Y (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
    #                 height=700,
    #                 width=700
    #             )
    #
    #             plot_fig.update_traces(
    #                 colorbar=dict(
    #                     tickfont=dict(size=20),
    #                     titlefont=dict(size=25),
    #                     thickness=20
    #                 )
    #             )
    #
    #             # heatmap_fig.write_image(folderpath / heatmap_fig.layout.title.text, format="pdf")
    #             plot_fig.write_image(folderpath / 'plot.png', format="png")
    #
    #             return f'Saved plot to png at {folderpath}'