import sys
from dash import Input, Output, State
import subprocess

from dash.exceptions import PreventUpdate

from modules.functions.functions_dektak import *

'''Callbacks for DEKTAK tab'''

def callbacks_dektak(app):

    # Callback to update profile plot based on heatmap click position
    @app.callback([Output('dektak_profile', 'figure', allow_duplicate=True),
                   Output('dektak_position_store', 'data')],
                  Input('dektak_heatmap', 'clickData'),
                  State('dektak_path_store', 'data'),
                  prevent_initial_call=True
                  )
    def update_position(heatmapclick, folderpath):
        folderpath = Path(folderpath)
        if heatmapclick is None:
            return go.Figure(), {}
        target_x = heatmapclick['points'][0]['x']
        target_y = heatmapclick['points'][0]['y']

        position = (target_x, target_y)

        # Plot the profile
        try:
            profile = profile_plot(folderpath, target_x, target_y)
        except NameError:
            return go.Figure(), {}

        return profile, position


    # Callback to refit profile plot
    @app.callback(
        [Output('dektak_profile', 'figure', allow_duplicate=True),
        Output('dektak_parameters_store', 'data')],
        Input('dektak_fit_button', 'n_clicks'),
        State('dektak_path_store', 'data'),
        State('dektak_position_store', 'data'),
        State('dektak_fit_start', 'value'),
        State('dektak_fit_height', 'value'),
        State('dektak_fit_stepnb', 'value'),
        prevent_initial_call=True
                  )
    def refit_profile(n_clicks, folderpath, position, start, height, stepnb):
        folderpath = Path(folderpath)
        if position is None:
            return go.Figure(), {}

        target_x = position[0]
        target_y = position[1]

        if n_clicks > 0:
            asc2d_dataframe = pd.read_csv(get_asc2d_path(folderpath, target_x, target_y), skiprows = 46)
            _, asc2d_dataframe = treat_data(asc2d_dataframe)
            guess = generate_parameters(x0=start, height=height, n_steps=stepnb)
            fitted_params = fit_data(asc2d_dataframe, guess)
            profile = profile_plot(folderpath, target_x, target_y)
            profile = fit_plot(profile, asc2d_dataframe, *fitted_params)

            return profile, fitted_params

        else:
            return go.Figure(), {}

    # Callback to save refitted profile
    @app.callback(
        Output('dektak_text_box', 'children', allow_duplicate=True),
        Input('dektak_save_button', 'n_clicks'),
        State('dektak_path_store', 'data'),
        State('dektak_position_store', 'data'),
        State('dektak_parameters_store', 'data'),
        prevent_initial_call=True
                  )
    def save_new_fit(n_clicks, folderpath, position, fitted_params):
        folderpath = Path(folderpath)
        if fitted_params is None:
            raise PreventUpdate

        target_x = position[0]
        target_y = position[1]

        if n_clicks > 0:
            replace_fit(folderpath, target_x, target_y, fitted_params)
            return (f'Replacement successful on database at {folderpath} for x = {target_x}, y = {target_y}')



    # Callback for heatmap plot selection
    @app.callback(
        Output('dektak_heatmap', 'figure', allow_duplicate=True),
        Input('dektak_heatmap_select', 'value'),
        Input('dektak_path_store', 'data'),
        prevent_initial_call=True
    )
    def update_heatmap(selected_plot, folderpath):
        folderpath = Path(folderpath)
        database_path = get_database_path(folderpath)
        if database_path is None:
            return go.Figure()
        try:
            database = pd.read_csv(database_path)
        except FileNotFoundError:
            return go.Figure()
        if database is None:
            return go.Figure()
        heatmap = heatmap_plot(database, mode=selected_plot, title=folderpath.name)
        return heatmap


    # Callback for batch fitting
    @app.callback(
        Output('dektak_text_box', 'children', allow_duplicate=True),
        Input('dektak_fit_button', 'n_clicks'),
        Input('dektak_path_store', 'data'),
        prevent_initial_call=True
    )
    def batch_fit_dektak(n_clicks, folderpath):
        folderpath = Path(folderpath)
        database_path = get_database_path(folderpath)
        if database_path is None and n_clicks > 0:
            command = [sys.executable, 'modules/functions/batch_fit_dektak.py']
            command.append(folderpath)
            # Launch the script in a new terminal
            if sys.platform == 'win32':  # Windows
                subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", "-a", "Terminal", "--args"] + command)
            elif sys.platform == "linux" or sys.platform == "linux2":  # Linux with gnome-terminal
                subprocess.Popen(["gnome-terminal", "--"] + command)
            else:
                return "Unsupported OS"
            return "Batch fitting has started in a separate python instance"

        elif database_path is None:
            return 'Database not found, press "Fit!" to launch batch fitting'

        else:
            return f"Database {get_database_path(folderpath)} loaded successfully"

