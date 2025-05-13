from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots

from ..functions.functions_profil import *

"""Callbacks for profil tab"""


def callbacks_profil(app):

    # Callback to update current position based on heatmap click
    @app.callback(
        Output("profil_position_store", "data"),
        Input("profil_heatmap", "clickData"),
        prevent_initial_call=True,
    )
    def profil_update_position(clickData):
        if clickData is None:
            return None
        target_x = clickData["points"][0]["x"]
        target_y = clickData["points"][0]["y"]

        position = (target_x, target_y)

        return position

    # Callback to find all relevant datasets in HDF5 file
    @app.callback(
        [Output("profil_select_dataset", "options"),
         Output("profil_select_dataset", "value")],
        Input("hdf5_path_store", "data"),
    )
    def profil_scan_hdf5_for_datasets(hdf5_path):
        with h5py.File(hdf5_path, "r") as hdf5_file:
            dataset_list = get_hdf5_datasets(hdf5_file, dataset_type='profil')

        return dataset_list, dataset_list[0]


    # Callback to check if HDF5 has results
    @app.callback(
        Output("profil_text_box", "children", allow_duplicate=True),
        Input("profil_select_dataset", "value"),
        State("hdf5_path_store", "data"),
        prevent_initial_call=True,
    )
    def profil_check_for_results(selected_dataset, hdf5_path):
        if selected_dataset is None:
            raise PreventUpdate

        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            if check_group_for_results(profil_group, mode='all'):
                return 'Found results for all points'
            elif check_group_for_results(profil_group, mode='any'):
                return 'Found results for some points'
            else:
                return'No results found'


    # Callback for heatmap plot selection
    @app.callback(
        [
            Output("profil_heatmap", "figure", allow_duplicate=True),
            Output("profil_heatmap_min", "value"),
            Output("profil_heatmap_max", "value"),
        ],
        Input("profil_heatmap_select", "value"),
        Input("profil_heatmap_min", "value"),
        Input("profil_heatmap_max", "value"),
        Input("profil_heatmap_precision", "value"),
        Input("profil_heatmap_edit", "value"),
        Input('hdf5_path_store', 'data'),
        Input("profil_select_dataset", "value"),
        prevent_initial_call=True,
    )
    def profil_update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path, selected_dataset):
        hdf5_path = Path(hdf5_path)
        if hdf5_path is None:
            raise PreventUpdate

        if ctx.triggered_id in ["profil_heatmap_select", "profil_heatmap_edit", "profil_heatmap_precision"]:
            z_min = None
            z_max = None

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            profil_df = profil_make_results_dataframe_from_hdf5(profil_group)

        masking = True
        if edit_toggle in ["edit", "unfiltered"]:
            masking = False

        fig = make_heatmap_from_dataframe(profil_df, values=heatmap_select, z_min=z_min, z_max=z_max, precision=precision)

        z_min = np.round(fig.data[0].zmin, precision)
        z_max = np.round(fig.data[0].zmax, precision)

        return fig, z_min, z_max

    # Profile plot
    @app.callback(
        Output("profil_plot", "figure"),
        Input("hdf5_path_store", "data"),
        Input("profil_position_store", "data"),
        Input("profil_plot_select", "value"),
        Input("profil_select_dataset", "value"),
    )
    def profil_update_plot(hdf5_path, position, plot_options, selected_dataset):
        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate
        if position is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            measurement_df = profil_get_measurement_from_hdf5(profil_group, target_x, target_y)
            results_dict = profil_get_results_from_hdf5(profil_group, target_x, target_y)

        _, measurement_df = profil_measurement_dataframe_treat(measurement_df, slope=results_dict['adjusting_slope'])

        options_dict = {}
        if 'adjusting_slope' in plot_options:
            options_dict['adjusting_slope'] = results_dict['adjusting_slope']
        if 'fit_parameters' in plot_options:
            options_dict['fit_parameters'] = results_dict['fit_parameters']


        # Plot the data
        fig = make_subplots(
            rows=3,
            cols=1,
            row_heights=[0.3, 0.4, 0.3],
            subplot_titles=("Total profile", "Fitted data", "Measured thicknesses"),
            shared_xaxes=True,
            vertical_spacing=0.1
        )

        fig = profil_plot_total_profile_from_dataframe(fig, measurement_df, options_dict)
        fig = profil_plot_adjusted_profile_from_dataframe(fig, measurement_df, options_dict)
        fig = profil_plot_measured_heights_from_dict(fig, results_dict)

        fig.update_layout(plot_layout(title=''))

        return fig


    # Refitting results
    @app.callback(
        [Output("profil_text_box", "children", allow_duplicate=True),
         Output("hdf5_path_store", "data", allow_duplicate=True)],
        Input("profil_fit_button", "n_clicks"),
        State("profil_fit_height", "value"),
        State("profil_fit_nb_steps", "value"),
        State("hdf5_path_store", "data"),
        State("profil_select_dataset", "value"),
        prevent_initial_call=True,
    )

    def profil_refit_data(n_clicks, fit_height, fit_degree, hdf5_path, selected_dataset):
        hdf5_path = Path(hdf5_path)

        if hdf5_path is None:
            raise PreventUpdate

        if n_clicks > 0:
            with h5py.File(hdf5_path, 'a') as hdf5_file:
                profil_group = hdf5_file[selected_dataset]
                check = profil_batch_fit_steps(profil_group, fit_height, fit_degree)
            if check:
                return 'Successfully refitted data', hdf5_path