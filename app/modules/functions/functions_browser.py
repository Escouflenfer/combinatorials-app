import datetime
import os
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback_context, dcc, html
from dash.exceptions import PreventUpdate

from modules.interface.icons import icons

def icon_file(app, extension, width=24, height=24):
    """Retrun an html.img of the svg icon for a given extension."""
    filetype = icons.get(extension)
    file_name = f'file_type_{filetype}.svg' if filetype is not None else 'default_file.svg'
    html_tag = html.Img(src=app.get_asset_url(f'icons/{file_name}'),
                        width=width, height=height)
    return html_tag


def nowtimestamp(timestamp, fmt='%b %d, %Y %H:%M'):
    return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)


def file_info(path):
    """Get file info for a given path.

    Uncomment the attributes that you want to display.

    Parameters:
    -----------
    path : pathlib.Path object
    """
    file_stat = path.stat()
    d = {
        'extension': path.suffix if not path.name.startswith('.') else path.name,
        'filename': path.name,
        # 'fullpath': str(path.absolute()),
        'size': format(file_stat.st_size, ','),
        'created': nowtimestamp(file_stat.st_ctime),
        'modified': nowtimestamp(file_stat.st_mtime),
        # 'accessed': nowtimestamp(file_stat.st_atime),
        # 'is_dir': str(path.is_dir()),
        # 'is_file': str(path.is_file()),
    }
    return d
