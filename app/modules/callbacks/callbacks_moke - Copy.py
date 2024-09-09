from dash import Input, Output

import modules.functions.functions_moke as moke

'''Callbacks for MOKE tab'''

def callbacks_moke(app, children_moke):

    # MOKE components
    @app.callback(
        Output(children_moke.subfolder_id, "options"),
        Input('moke_path_store', "data"),
    )
    def update_subfolder_moke(folderpath):
        subfolder_options = []
        if folderpath is not None:
            subfolder_options = moke.get_subfolders(
                folderpath, moke_path=children_moke.folderpath_dataPath
            )

        return subfolder_options

    # @app.callback(
    #     Output("moke", "children"),
    #     Input(children_moke.data_type_id, "value"),
    #     Input(children_moke.folderpath_id, "value"),
    #     Input(children_moke.subfolder_id, "value"),
    # )
    # def update_sliders_moke(data_type, folderpath, subfolder):
    #     print(data_type, children_moke.data_type_value)
    #     if children_moke.data_type_value == data_type:
    #         return children_moke
    #     else:
    #         children_moke.data_type_value = data_type
    #
    #     new_children_moke = widgets_moke.WidgetsMOKE()
    #     new_children_moke.folderpath_value = folderpath
    #     new_children_moke.subfolder_options = update_subfolder_moke(folderpath)
    #     new_children_moke.subfolder_value = subfolder
    #
    #     if data_type == "Magnetic properties":
    #         new_children_moke.set_properties_to_magnetic()
    #
    #     elif data_type == "Raw MOKE data":
    #         new_children_moke.set_properties_to_raw()
    #
    #     return new_children_moke.get_children()

    #   MOKE
    @app.callback(
        Output(children_moke.moke_heatmap_id, "figure"),
        Input('moke_path_store', "data"),
        Input(children_moke.subfolder_id, "value"),
        Input(children_moke.data_type_id, "value"),
    )
    def update_heatmap_moke(foldername, subfolder, datatype):
        fig, header_data = moke.plot_moke_heatmap(foldername, subfolder, datatype)
        # Update the dimensions of the heatmap and the X-Y title axes
        fig.update_layout(height=500, width=500, clickmode="event+select")
        fig.update_xaxes(title="X Position")
        fig.update_yaxes(title="Y Position")

        fig.data[0].colorbar = dict(title=header_data)

        return fig

    #   MOKE data
    @app.callback(
        Output(children_moke.moke_loop_id, "figure"),
        Input('moke_path_store', "data"),
        Input(children_moke.subfolder_id, "value"),
        Input(children_moke.moke_heatmap_id, "clickData"),
        Input(children_moke.xrange_slider_id, "value"),
        Input(children_moke.yrange_slider_id, "value"),
        Input(children_moke.data_type_id, "value"),
    )
    def update_moke_data(foldername, subfolder, clickData, xrange, yrange, data_type):
        if clickData is None:
            x_pos, y_pos = 0, 0
        else:
            x_pos = int(clickData["points"][0]["x"])
            y_pos = int(clickData["points"][0]["y"])

        fig = moke.plot_1D_with_datatype(foldername, subfolder, x_pos, y_pos, data_type)

        fig.update_layout(
            height=500,
            width=1100,
            title=f"MOKE Signal for {subfolder} at position ({x_pos}, {y_pos})",
        )
        fig.update_xaxes(title="Time (μs)", range=xrange)
        fig.update_yaxes(title="Kerr Rotation (V)", range=yrange)

        return fig