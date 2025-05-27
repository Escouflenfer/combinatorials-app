import dash_uploader
from dash import Dash, dcc, html
from setuptools.compat.py311 import shutil_rmtree

from modules.functions.functions_shared import *

from modules.interface import (
    widgets_browser,
    widgets_profil,
    widgets_edx,
    widgets_moke,
    widgets_xrd,
    widgets_hdf5,
)
from modules.callbacks import (
    callbacks_browser,
    callbacks_profil,
    callbacks_edx,
    callbacks_moke,
    callbacks_xrd,
    callbacks_hdf5,
)

pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)

folderpath = None

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

PROGRAM_VERSION = '0.12 beta'
UPLOAD_FOLDER_ROOT = os.path.join(script_dir, "uploads")

# Clean the upload folder
cleanup_directory(UPLOAD_FOLDER_ROOT)

# %%
app = Dash(suppress_callback_exceptions=True)

dash_uploader.configure_upload(app, UPLOAD_FOLDER_ROOT)

children_browser = widgets_browser.WidgetsBROWSER()
browser_tab = children_browser.make_tab_from_widgets()

children_hdf5 = widgets_hdf5.WidgetsHDF5(UPLOAD_FOLDER_ROOT)
hdf5_tab = children_hdf5.make_tab_from_widgets()

children_profil = widgets_profil.WidgetsPROFIL()
profil_tab = children_profil.make_tab_from_widgets()

children_edx = widgets_edx.WidgetsEDX()
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
            children=[browser_tab, hdf5_tab, profil_tab, edx_tab, moke_tab, xrd_tab],
        )
    ],
    className="window_layout",
)


callbacks_browser.callbacks_browser(app)
callbacks_hdf5.callbacks_hdf5(app)
callbacks_profil.callbacks_profil(app)
callbacks_edx.callbacks_edx(app)
callbacks_moke.callbacks_moke(app, children_moke)
callbacks_xrd.callbacks_xrd(app, children_xrd)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
