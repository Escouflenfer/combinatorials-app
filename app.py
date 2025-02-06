import os

from dash import Dash, dcc, html

from modules.interface import (
    widgets_browser,
    widgets_dektak,
    widgets_edx,
    widgets_moke,
    widgets_xrd,
    widgets_hdf5,
)
from modules.callbacks import (
    callbacks_browser,
    callbacks_dektak,
    callbacks_edx,
    callbacks_moke,
    callbacks_xrd,
    callbacks_hdf5,
)


folderpath = None

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# %%
app = Dash(suppress_callback_exceptions=True)

children_browser = widgets_browser.WidgetsBROWSER()
browser_tab = children_browser.make_tab_from_widgets()

children_hdf5 = widgets_hdf5.WidgetsHDF5(folderpath)
hdf5_tab = children_hdf5.make_tab_from_widgets()

children_dektak = widgets_dektak.WidgetsDEKTAK(folderpath)
dektak_tab = children_dektak.make_tab_from_widgets()

children_edx = widgets_edx.WidgetsEDX(folderpath)
edx_tab = children_edx.make_tab_from_widgets()

children_moke = widgets_moke.WidgetsMOKE(folderpath)
moke_tab = children_moke.make_tab_from_widgets()

children_xrd = widgets_xrd.WidgetsXRD(folderpath)
xrd_tab = children_xrd.make_tab_from_widgets()


# Defining the main window layout
app.layout = html.Div(
    [
        dcc.Tabs(
            id="tabs",
            value="browser",
            children=[browser_tab, hdf5_tab, dektak_tab, edx_tab, moke_tab, xrd_tab],
        )
    ],
    className="window_layout",
)


callbacks_browser.callbacks_browser(app)
callbacks_hdf5.callbacks_hdf5(app)
callbacks_dektak.callbacks_dektak(app)
callbacks_edx.callbacks_edx(app)
callbacks_moke.callbacks_moke(app, children_moke)
callbacks_xrd.callbacks_xrd(app, children_xrd)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
