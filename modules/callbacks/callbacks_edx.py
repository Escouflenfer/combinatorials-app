from dash import Input, Output, State, ctx
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
    @app.callback([Output("element_edx", "options"),
                   Output("element_edx", "value")],
                  Input("edx_path_store", "data"))
    def update_element_edx(hdf5_path):
        if hdf5_path is None:
            raise PreventUpdate
        edx_element_list = get_quantified_elements(hdf5_path)
        return edx_element_list, edx_element_list[0]

    # Callback to plot EDX heatmap
    @app.callback(
        [Output("edx_heatmap", "figure"),
         Output('edx_heatmap_min', 'value'),
         Output('edx_heatmap_max', 'value')],
        Input("element_edx", "value"),
        Input('edx_heatmap_min', 'value'),
        Input('edx_heatmap_max', 'value'),
        Input('edx_heatmap_precision', 'value'),
        State("edx_path_store", "data"),
    )
    def update_heatmap_edx(element_edx, z_min, z_max, precision, hdf5_path):
        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate

        if ctx.triggered_id in ['element_edx', 'edx_heatmap_precision'] :
            z_min = None
            z_max = None

        edx_df = edx_make_results_dataframe_from_hdf5(hdf5_path)
        fig = edx_make_heatmap_from_dataframe(edx_df, values=element_edx, z_min=z_min, z_max=z_max, precision=precision)

        z_min = np.round(fig.data[0].zmin, precision)
        z_max = np.round(fig.data[0].zmax, precision)

        # Update the dimensions of the heatmap and the X-Y title axes
        # sample_name = folderpath.parent.name
        # layout=heatmap_layout('EDX Composition Map <br>' + sample_name)
        # fig.update_layout(layout)

        return fig, z_min, z_max


    #   EDX spectra
    @app.callback(
        Output("edx_spectra", "figure"),
        Input("edx_path_store", "data"),
        Input("edx_position_store", "data"),
    )
    def update_spectra(hdf5_path, position):
        if hdf5_path is None:
            raise PreventUpdate
        if position is None:
            raise PreventUpdate

        hdf5_path = Path(hdf5_path)

        target_x = position[0]
        target_y = position[1]

        spectrum_df = get_spectra_from_hdf5(hdf5_path, target_x, target_y)
        fig = plot_spectra_from_dataframe(spectrum_df)

        return fig
