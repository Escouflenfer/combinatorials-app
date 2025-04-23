from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate

from ..functions.functions_edx import *

def callbacks_edx(app):

    # Callback to update position based on heatmap click
    @app.callback(Output('edx_position_store', 'data'),
                  Input('edx_heatmap', 'clickData'),
                  prevent_initial_call=True
                  )
    def edx_update_position(heatmapclick):
        if heatmapclick is None:
            return None
        target_x = heatmapclick['points'][0]['x']
        target_y = heatmapclick['points'][0]['y']

        position = (target_x, target_y)

        return position


    # Callback to get elements for the dropdown menu
    @app.callback([Output("edx_heatmap_select", "options"),
                   Output("edx_heatmap_select", "value")],
                  Input("hdf5_path_store", "data"))
    def edx_update_element_list(hdf5_path):
        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file['edx']
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
        State("hdf5_path_store", "data"),
    )
    def edx_update_heatmap(heatmap_select, z_min, z_max, precision, hdf5_path):
        hdf5_path = Path(hdf5_path)
        if hdf5_path is None:
            raise PreventUpdate

        if ctx.triggered_id in ['edx_heatmap_select', 'edx_heatmap_precision'] :
            z_min = None
            z_max = None

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file['edx']
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
        Input("hdf5_path_store", "data"),
        Input("edx_position_store", "data"),
    )
    def edx_update_plot(hdf5_path, position):
        hdf5_path = Path(hdf5_path)
        if hdf5_path is None:
            raise PreventUpdate
        if position is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            edx_group = hdf5_file['edx']
            measurement_df = edx_get_measurement_from_hdf5(edx_group, target_x, target_y)

        fig = edx_plot_measurement_from_dataframe(measurement_df)

        return fig
