from ..functions.functions_profil import *
from dash import html, dcc

from ..hdf5_compilers.hdf5compile_base import safe_create_new_subgroup

"""Callbacks for profil tab"""


def callbacks_profil(app):

    # Callback to update current position based on heatmap click
    @app.callback(
        Output("profil_position_store", "data"),
        Input("profil_heatmap", "clickData"),
        prevent_initial_call=True,
    )
    def profil_update_position(heatmap_click):
        if heatmap_click is None:
            return None
        target_x = heatmap_click["points"][0]["x"]
        target_y = heatmap_click["points"][0]["y"]

        position = (target_x, target_y)

        return position

    # Callback to find all relevant datasets in HDF5 file
    @app.callback(
        [Output("profil_select_dataset", "options"),
         Output("profil_select_dataset", "value")],
        Input("hdf5_path_store", "data"),
    )
    @check_conditions(profil_conditions, hdf5_path_index=0)
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
    @check_conditions(profil_conditions, hdf5_path_index=1)
    def profil_check_for_results(selected_dataset, hdf5_path):
        if selected_dataset is None:
            raise PreventUpdate

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            if check_group_for_results(profil_group):
                return 'Found results for all points'
            return'No results found'


    # Callback for heatmap plot selection
    @app.callback(
        [
            Output("profil_heatmap", "figure", allow_duplicate=True),
            Output("profil_heatmap_min", "value"),
            Output("profil_heatmap_max", "value"),
            Output("profil_heatmap_select", "options"),
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
    @check_conditions(profil_conditions, hdf5_path_index=5)
    def profil_update_heatmap(heatmap_select, z_min, z_max, precision, edit_toggle, hdf5_path, selected_dataset):
        if ctx.triggered_id in ["profil_heatmap_select", "profil_heatmap_edit", "profil_heatmap_precision"]:
            z_min = None
            z_max = None

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            profil_df = profil_make_results_dataframe_from_hdf5(profil_group)

        masking = True
        if edit_toggle in ["edit", "unfiltered"]:
            masking = False

        fig = make_heatmap_from_dataframe(profil_df, values=heatmap_select, z_min=z_min, z_max=z_max,
                                          precision=precision, masking=masking)

        z_min = np.round(fig.data[0].zmin, precision)
        z_max = np.round(fig.data[0].zmax, precision)

        options = list(profil_df.columns[3:])
        if "default" in options:
            options.remove("default")

        return fig, z_min, z_max, profil_df.columns[7:]

    # Profile plot
    @app.callback(
        Output("profil_plot", "figure"),
        Input("profil_select_dataset", "value"),
        Input("profil_position_store", "data"),
        Input("profil_plot_select", "value"),
        State("hdf5_path_store", "data"),
    )
    @check_conditions(profil_conditions, hdf5_path_index=3)
    def profil_update_plot(selected_dataset, position, plot_options, hdf5_path):
        if position is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        # Plot the data
        fig = make_subplots(
            rows=3,
            cols=1,
            row_heights=[0.3, 0.4, 0.3],
            subplot_titles=("Total profile", "Fitted data", "Measured thicknesses"),
            shared_xaxes=True,
            vertical_spacing=0.1
        )

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            measurement_df = profil_get_measurement_from_hdf5(profil_group, target_x, target_y)
            results_dict = profil_get_results_from_hdf5(profil_group, target_x, target_y)

        adjusting_slope = None
        fit_parameters = None
        if results_dict:
            adjusting_slope = results_dict["adjusting_slope"]
            fit_parameters = results_dict["fit_parameters"]

        adjusting_slope, measurement_df = profil_measurement_dataframe_treat(measurement_df, adjusting_slope)

        if "adjusting_slope" not in plot_options:
            adjusting_slope = None
        fig = profil_plot_total_profile_from_dataframe(fig, measurement_df, adjusting_slope)

        if "fit_parameters" not in plot_options:
            fit_parameters = None
        fig = profil_plot_adjusted_profile_from_dataframe(fig, measurement_df, fit_parameters)

        if results_dict:
            fig = profil_plot_measured_heights_from_dict(fig, results_dict)

        fig.update_layout(plot_layout(title=''))

        return fig


    # Refitting results
    @app.callback(
        Output("profil_text_box", "children", allow_duplicate=True),
        Input("profil_fit_button", "n_clicks"),
        State("profil_select_fit_mode", "value"),
        State("profil_fit_nb_steps", "value"),
        State("profil_fit_x0", "value"),
        State("hdf5_path_store", "data"),
        State("profil_select_dataset", "value"),
        State("profil_position_store", "data"),
        prevent_initial_call=True,
    )
    @check_conditions(profil_conditions, hdf5_path_index=4)
    def profil_refit_data(n_clicks, fit_mode, nb_steps, x0, hdf5_path, selected_dataset, target_position):
        if n_clicks > 0:
            if fit_mode == "Batch fitting":
                with h5py.File(hdf5_path, 'a') as hdf5_file:
                    profil_group = hdf5_file[selected_dataset]
                    for position, position_group in profil_group.items():
                        check = profil_spot_fit_steps(position_group, nb_steps, x0)
                return 'Successfully refitted data'

            if fit_mode == "Spot fitting":
                with h5py.File(hdf5_path, 'a') as hdf5_file:
                    profil_group = hdf5_file[selected_dataset]
                    position_group = get_target_position_group(profil_group, target_position[0], target_position[1])
                    check = profil_spot_fit_steps(position_group, nb_steps, x0)
                if check:
                    return f"Successfully refitted position {target_position}"
            if fit_mode == "Manual":
                with h5py.File(hdf5_path, 'a') as hdf5_file:
                    profil_group = hdf5_file[selected_dataset]
                    position_group = get_target_position_group(profil_group, target_position[0], target_position[1])
                    results_group = safe_create_new_subgroup(position_group, new_subgroup_name="results")


    
    # Callback to deal with heatmap edit mode
    @app.callback(
        Output('profil_text_box', 'children', allow_duplicate=True),
        Input('profil_heatmap', 'clickData'),
        State('profil_heatmap_edit', 'value'),
        State('hdf5_path_store', 'data'),
        State('profil_select_dataset', 'value'),
        prevent_initial_call=True
    )
    @check_conditions(profil_conditions, hdf5_path_index=2)
    def heatmap_edit_mode(heatmap_click, edit_toggle, hdf5_path, selected_dataset):
        if edit_toggle != 'edit':
            raise PreventUpdate

        target_x = heatmap_click['points'][0]['x']
        target_y = heatmap_click['points'][0]['y']

        with h5py.File(hdf5_path, 'a') as hdf5_file:
            profil_group = hdf5_file[selected_dataset]
            position_group = get_target_position_group(profil_group, target_x, target_y)
            if not position_group.attrs["ignored"]:
                position_group.attrs["ignored"] = True
                return f"{target_x}, {target_y} ignore set to True"
            else:
                position_group.attrs["ignored"] = False
                return f"{target_x}, {target_y} ignore set to False"


    # Callback for fit modes
    @app.callback(
        Output("profil_fit_inputs", "children"),
        Input("profil_select_fit_mode", "value"),
    )
    def profil_fitting_interface(selected_mode):
        if selected_mode in ["Spot fitting", "Batch fitting"]:
            new_children = [
                dcc.Input(id="profil_fit_nb_steps", className="long-item", type="number", placeholder="Number of steps", value=None),
                dcc.Input(id="profil_fit_x0", className="long-item", type="number", placeholder="First step position", value=None),
            ]
        else:
            new_children = [
                dcc.Input(id="profil_fit_height", className="long-item", type="number", placeholder="Height", value=None),
            ]
        return new_children
