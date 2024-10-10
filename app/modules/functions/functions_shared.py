import numpy as np
import plotly.graph_objects as go


def heatmap_layout(title = ''):
    """
    Generates a standardized layout for all heatmaps.

    Parameters:
        title (str): The title of the plot.

    Returns:
        go.Layout(): layout object that can be passed to a figure
    """
    layout = go.Layout(
        title=title,
        titlefont=dict(size=20),
        xaxis=dict(title='X (mm)', tickfont=dict(size=15), titlefont=dict(size=18)),
        yaxis=dict(title='Y (mm)', tickfont=dict(size=15), titlefont=dict(size=18)),
        height=750,
        width=750
    )
    return layout

def plot_layout(title = ''):
    """
    Generates a standardized layout for all plots.

    Parameters:
        title (str): The title of the plot.

    Returns:
        go.Layout(): layout object that can be passed to a figure
    """
    layout = go.Layout(
        height=750,
        width=1100,
        title=title,
        showlegend=False
    )
    return layout

def colorbar_layout(z_min, z_max, title=''):
    z_mid = (z_min + z_max)/2
    colorbar = dict(
        title=f'{title} <br>&nbsp;<br>',
        tickfont=dict(size=15),
        titlefont=dict(size=18),
        tickvals=[z_min, (z_min + z_mid) / 2, z_mid, (z_max + z_mid) / 2, z_max],  # Tick values
        ticktext=[f'{z_min:.2f}', f'{(z_min + z_mid) / 2:.2f}', f'{z_mid:.2f}', f'{(z_max + z_mid) / 2:.2f}',
                  f'{z_max:.2f}'],  # Tick text
    )
    return colorbar

def significant_round(num, sig_figs):
    """
    Rounds a number to a specified number of significant figures.

    Parameters:
        num (float): The number to round.
        sig_figs (int): The number of significant figures to round to.

    Returns:
        float: The rounded number.
    """
    if num == 0:
        return 0  # Special case for zero

    # Calculate the factor to shift the decimal point
    shift_factor = np.pow(10, sig_figs - np.ceil(np.log10(abs(num))))

    # Shift number, round, and shift back
    return round(num * shift_factor) / shift_factor