from modules.functions.functions_browser import *


'''Callbacks for file browser'''
def callbacks_browser(app):
    @app.callback(
        Output('cwd', 'children'),
        Input('stored_cwd', 'data'),
        Input('parent_dir', 'n_clicks'),
        Input('cwd', 'children'),
        prevent_initial_call=True)
    def get_parent_directory(stored_cwd, n_clicks, currentdir):
        triggered_id = callback_context.triggered_id
        if triggered_id == 'stored_cwd':
            return stored_cwd
        parent = Path(currentdir).parent.as_posix()
        return parent


    @app.callback(
        Output('cwd_files', 'children'),
        Input('cwd', 'children'))
    def list_cwd_files(cwd):
        path = Path(cwd)
        all_file_details = []
        if path.is_dir():
            files = sorted(os.listdir(path), key=str.lower)
            for i, file in enumerate(files):
                filepath = Path(file)
                full_path = os.path.join(cwd, filepath.as_posix())
                is_dir = Path(full_path).is_dir()
                link = html.A([
                    html.Span(
                        file, id={'type': 'listed_file', 'index': i},
                        title=full_path,
                        style={'fontWeight': 'bold', 'fontSize': 18} if is_dir else {}
                    )], href='#')
                details = file_info(Path(full_path))
                details['filename'] = link
                if is_dir:
                    details['extension'] = html.Img(
                        src=app.get_asset_url('icons/default_folder.svg'),
                        width=25, height=25)
                else:
                    details['extension'] = icon_file(app, details['extension'][1:])
                all_file_details.append(details)

        df = pd.DataFrame(all_file_details)
        df = df.rename(columns={"extension": ''})
        table = dbc.Table.from_dataframe(df, striped=False, bordered=False,
                                         hover=True, size='sm')
        return html.Div(table)


    @app.callback(
        Output('stored_cwd', 'data'),
        Input({'type': 'listed_file', 'index': ALL}, 'n_clicks'),
        State({'type': 'listed_file', 'index': ALL}, 'title'))
    def store_clicked_file(n_clicks, title):
        if not n_clicks or set(n_clicks) == {None}:
            raise PreventUpdate
        ctx = callback_context
        index = ctx.triggered_id['index']
        return title[index]

    # Callback to set folder path
    @app.callback(
        [Output('sample_path_store', 'data'),
         Output('sample_path_text', 'children')],
        Input('sample_path_button', 'n_clicks'),
        State('sample_path_store', 'data'),
        State('stored_cwd', 'data'))

    def set_folder_path(n_clicks, stored_folder_path, current_folder_path):
        if n_clicks == None:
            return stored_folder_path, str(stored_folder_path)
        elif n_clicks > 0:
            return current_folder_path, str(current_folder_path)


    # Callback for EDX folder path
    @app.callback(
        [Output('edx_path_store', 'data'),
         Output('edx_path_text', 'children')],
        Input('edx_path_button', 'n_clicks'),
        State('edx_path_store', 'data'),
        State('stored_cwd', 'data'))
    def set_folder_path(n_clicks, stored_folder_path, current_folder_path):
        if n_clicks == None:
            return stored_folder_path, str(stored_folder_path)
        elif n_clicks > 0:
            return current_folder_path, str(current_folder_path)

    # Callback for DEKTAK folder path
    @app.callback(
        [Output('dektak_path_store', 'data'),
         Output('dektak_path_text', 'children')],
        Input('dektak_path_button', 'n_clicks'),
        State('dektak_path_store', 'data'),
        State('stored_cwd', 'data'))
    def set_folder_path(n_clicks, stored_folder_path, current_folder_path):
        if n_clicks == None:
            return stored_folder_path, str(stored_folder_path)
        elif n_clicks > 0:
            return current_folder_path, str(current_folder_path)

    # Callback for MOKE folder path
    @app.callback(
        [Output('moke_path_store', 'data'),
         Output('moke_path_text', 'children')],
        Input('moke_path_button', 'n_clicks'),
        State('moke_path_store', 'data'),
        State('stored_cwd', 'data'))
    def set_folder_path(n_clicks, stored_folder_path, current_folder_path):
        if n_clicks == None:
            return stored_folder_path, str(stored_folder_path)
        elif n_clicks > 0:
            return current_folder_path, str(current_folder_path)

    # Callback for xrd folder path
    @app.callback(
        [Output('xray_path_store', 'data'),
         Output('xray_path_text', 'children')],
        Input('xray_path_button', 'n_clicks'),
        State('xray_path_store', 'data'),
        State('stored_cwd', 'data'))
    def set_folder_path(n_clicks, stored_folder_path, current_folder_path):
        if n_clicks == None:
            return stored_folder_path, str(stored_folder_path)
        elif n_clicks > 0:
            return current_folder_path, str(current_folder_path)