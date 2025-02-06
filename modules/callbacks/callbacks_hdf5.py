from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate

from ..functions.functions_hdf5 import *

def callbacks_hdf5(app):

    @app.callback(Output('hdf5_path_box', 'children'),
                  Input('hdf5_new', 'n_clicks'))

    def test_function(n_clicks):
        return str(n_clicks)