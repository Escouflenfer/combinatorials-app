"""
class file for edx widgets using dash module to detach it completely from Jupyter Notebooks.
Internal use for Institut Néel and within the MaMMoS project, to read big datasets produced at Institut Néel.

@Author: William Rigaut - Institut Néel (william.rigaut@neel.cnrs.fr)
"""

import os
from dash import html, dcc
from itertools import count, takewhile


def frange(start, stop, step):
    return takewhile(lambda x: x < stop, count(start, step))


class WidgetsMOKE:
    folderpath = None
    folderpath_id = "moke_folderpath"
    folderpath_value = None
    folderpath_label = "Folderpath"
    folderpath_dataPath = "./data/MOKE/"
    folderpath_className = "moke_cell12"

    subfolder_id = "moke_subfolder"
    subfolder_value = None
    subfolder_options = []
    subfolder_label = "Subfolder"
    subfolderpath_className = "moke_cell22"

    xrange_slider_id = "moke_xrange_slider"
    xrange_slider_label = "Time"
    xrange_slider_min = 0
    xrange_slider_max = 100
    xrange_slider_step = 1
    xrange_slider_value = [0, 100]
    xrange_slider_markStep = 10
    xrange_slider_className = "moke_cell13"

    yrange_slider_id = "moke_yrange_slider"
    yrange_slider_label = "Kerr rotation"
    yrange_slider_min = -1
    yrange_slider_max = 1
    yrange_slider_step = 0.01
    yrange_slider_value = [-0.5, 0.5]
    yrange_slider_markStep = 0.5
    yrange_slider_className = "moke_cell23"

    crange_slider_id = "moke_crange_slider"
    crange_slider_label = "Reflectivity (V)"
    crange_slider_min = 0
    crange_slider_max = 10
    crange_slider_step = 0.1
    crange_slider_value = [0, 3]
    crange_slider_markStep = 2
    crange_slider_className = "moke_cell21"

    data_type_id = "moke_data_type"
    data_type_label = "Data type"
    data_type_label_moke = "Raw MOKE data"
    data_type_label_magnetic = "Magnetic properties"
    data_type_value = "Raw MOKE data"
    data_type_className = "moke_cell11"

    moke_loop_id = "moke_loop"
    moke_loop_className = "moke_loop_plot_cell"

    moke_heatmap_id = "moke_heatmap"
    moke_heatmap_className = "moke_heatmap_plot_cell"

    def __init__(self):
        # Folderpath for the MOKE loop
        self.folderpath = html.Div(
            children=[
                html.Label(self.folderpath_label),
                dcc.Dropdown(
                    [
                        elm
                        for elm in os.listdir(self.folderpath_dataPath)
                        if not elm.startswith(".")
                    ],
                    value=self.folderpath_value,
                    id=self.folderpath_id,
                ),
            ],
            className=self.folderpath_className,
        )

        # Element component
        self.subfolder = html.Div(
            children=[
                html.Label(self.subfolder_label),
                dcc.Dropdown(
                    options=self.subfolder_options,
                    value=self.subfolder_value,
                    id=self.subfolder_id,
                ),
            ],
            className=self.subfolderpath_className,
        )

        # Slider Xrange component
        self.xrange_slider = html.Div(
            children=[
                html.Label(self.xrange_slider_label),
                dcc.RangeSlider(
                    min=self.xrange_slider_min,
                    max=self.xrange_slider_max,
                    step=self.xrange_slider_step,
                    value=self.xrange_slider_value,
                    marks={
                        i: f"{i}"
                        for i in range(
                            self.xrange_slider_min,
                            self.xrange_slider_max + self.xrange_slider_markStep,
                            self.xrange_slider_markStep,
                        )
                    },
                    id=self.xrange_slider_id,
                ),
            ],
            className=self.xrange_slider_className,
        )

        # Slider Yrange component
        self.yrange_slider = html.Div(
            children=[
                html.Label(self.yrange_slider_label),
                dcc.RangeSlider(
                    min=self.yrange_slider_min,
                    max=self.yrange_slider_max,
                    step=self.yrange_slider_step,
                    value=self.yrange_slider_value,
                    marks={
                        i: f"{i}"
                        for i in frange(
                            self.yrange_slider_min,
                            self.yrange_slider_max + self.yrange_slider_markStep,
                            self.yrange_slider_markStep,
                        )
                    },
                    id=self.yrange_slider_id,
                ),
            ],
            className=self.yrange_slider_className,
        )

        # Colorange for heatmap
        self.crange_slider = html.Div(
            children=[
                html.Label(self.crange_slider_label),
                dcc.RangeSlider(
                    min=self.crange_slider_min,
                    max=self.crange_slider_max,
                    step=self.crange_slider_step,
                    value=self.crange_slider_value,
                    marks={
                        i: f"{i}"
                        for i in frange(
                            self.crange_slider_min,
                            self.crange_slider_max + self.crange_slider_markStep,
                            self.crange_slider_markStep,
                        )
                    },
                    id=self.crange_slider_id,
                ),
            ],
            className=self.crange_slider_className,
        )

        self.data_type = html.Div(
            children=[
                html.Label(self.data_type_label),
                dcc.Dropdown(
                    options=[self.data_type_label_moke, self.data_type_label_magnetic],
                    value=self.data_type_value,
                    id=self.data_type_id,
                ),
            ],
            className=self.data_type_className,
        )

        # EDX spectra graph that will be modified by user interaction
        self.moke_loop = html.Div(
            [dcc.Graph(id=self.moke_loop_id)], className=self.moke_loop_className
        )

        # EDX heatmap
        self.moke_heatmap = html.Div(
            [dcc.Graph(id=self.moke_heatmap_id)], className=self.moke_heatmap_className
        )

    def set_properties_to_magnetic(self):
        self.crange_slider_label = "Coercivity (T)"
        self.crange_slider_min = 0
        self.crange_slider_max = 10
        self.crange_slider_markStep = 2

        self.xrange_slider_label = "Applied Field (T)"
        self.xrange_slider_min = -10
        self.xrange_slider_max = 10
        self.xrange_slider_markStep = 5
        self.xrange_slider_value = [-5, 5]

        self.yrange_slider_label = "MOKE Signal (V)"
        self.yrange_slider_min = -0.2
        self.yrange_slider_max = 0.2
        self.yrange_slider_markStep = 0.1
        self.yrange_slider_value = [-0.1, 0.1]

        self.data_type_value = "Magnetic properties"

        # Re-initializing component attributs after changing the base attributs
        self.__init__()

        return None

    def set_properties_to_raw(self):
        self.crange_slider_label = "Reflectivity (V)"
        self.crange_slider_min = 0
        self.crange_slider_max = 5
        self.crange_slider_markStep = 1

        self.xrange_slider_label = "Time"
        self.xrange_slider_min = 0
        self.xrange_slider_max = 100
        self.xrange_slider_markStep = 10
        self.xrange_slider_value = [0, 100]

        self.yrange_slider_label = "Kerr Rotation"
        self.yrange_slider_min = -1
        self.yrange_slider_max = 1
        self.yrange_slider_markStep = 0.5
        self.yrange_slider_value = [-0.5, 0.5]

        # Re-initializing component attributs after changing the base attributs
        self.__init__()

        return None

    def get_children(self, className_moke="grid_layout_moke"):
        children = (
            html.Div(
                [
                    self.folderpath,
                    self.subfolder,
                    self.crange_slider,
                    self.xrange_slider,
                    self.yrange_slider,
                    self.data_type,
                    self.moke_loop,
                    self.moke_heatmap,
                ],
                className=className_moke,
            ),
        )

        return children

    def make_tab_from_widgets(
        self,
        id_moke="moke",
        label_moke="MOKE",
        value_moke="moke",
        className_moke="grid_layout_moke",
    ):
        moke_tab = dcc.Tab(
            id=id_moke,
            label=label_moke,
            value=value_moke,
            children=[
                html.Div(
                    [
                        self.folderpath,
                        self.subfolder,
                        self.crange_slider,
                        self.xrange_slider,
                        self.yrange_slider,
                        self.data_type,
                        self.moke_loop,
                        self.moke_heatmap,
                    ],
                    className=className_moke,
                )
            ],
        )

        return moke_tab
