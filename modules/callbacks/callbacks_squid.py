import sys
from dash import Input, Output, State
import subprocess

from dash.exceptions import PreventUpdate

from modules.functions.functions_squid import *

'''Callbacks for SQUID tab'''

def callbacks_squid(app):

    # Callback to update files in dropdown:
    @app.callback(
        Output('squid_plot_select', 'options'),
        Input('squid_folder_store', 'data'),
    )
    
    def get_squid_files(folderpath):
        folderpath = Path(folderpath)
        file_list = []
        for file in folderpath.glob('*.dat'):
            file_list.append(file)
        return file_list

    # Callback to load file from dropdown
    @app.callback(
        [Output('squid_text_box', 'children', allow_duplicate=True),
        Output('squid_plot', 'figure', allow_duplicate=True)],
        Input('squid_plot_select', 'value'),
        State('squid_folder_store', 'data'),
        prevent_initial_call=True
    )

    def load_squid_file(folderpath):









    # Callback to save heatmap
    @app.callback(
        Output('squid_text_box', 'children', allow_duplicate=True),
        Input('squid_heatmap_save','n_clicks'),
        State('squid_heatmap', 'figure'),
        State('squid_path_store', 'data'),
        prevent_initial_call=True
        )

    def save_heatmap_to_pdf(n_clicks, heatmap_fig, folderpath):
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
        Output('squid_text_box', 'children', allow_duplicate=True),
        Input('squid_plot_save', 'n_clicks'),
        State('squid_plot', 'figure'),
        State('squid_path_store', 'data'),
        prevent_initial_call=True
    )
    def save_plot(n_clicks, plot_fig, folderpath):
        folderpath = Path(folderpath)
        plot_fig = go.Figure(plot_fig)
        if n_clicks > 0:
            plot_fig.update_layout(
                titlefont=dict(size=30),
                xaxis=dict(title='X (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
                yaxis=dict(title='Y (mm)', tickfont=dict(size=20), titlefont=dict(size=25)),
                height=700,
                width=1100
            )

            # heatmap_fig.write_image(folderpath / heatmap_fig.layout.title.text, format="pdf")
            plot_fig.write_image(folderpath / 'plot.png', format="png")

            return f'Saved plot to png at {folderpath}'