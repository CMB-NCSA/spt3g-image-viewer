# interactive_map.py

from dash import html, dcc
from dash import Output, Input, callback, callback_context
import dash
import plotly.graph_objects as go
from PIL import Image
from astropy.io import fits
from astropy.wcs import WCS
from astropy.visualization import simple_norm
from astropy.coordinates import SkyCoord
import astropy.units as u
import pandas as pd
import io
import base64

def pil_image_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    return "data:image/png;base64," + encoded

def create_map_figure(catalog_path=None,
                      catalog_df=None,
                      fits_path=None,
                      png_path=None,
                      png_path_local=None,
                      color_by='z'):
    # Load image and calculate size
    img = Image.open(png_path_local)
    png_width, png_height = img.size


    # Load catalog if not passed
    if catalog_df is None:
        if catalog_path is None:
            raise ValueError("Either catalog_df or catalog_path must be provided.")
        catalog_df = pd.read_csv(catalog_path)

    ra, dec = catalog_df["spt3g_ra(deg)"].values, catalog_df["spt3g_dec(deg)"].values
    data = fits.open(fits_path)[1].data
    wcs = WCS(fits.open(fits_path)[1].header)
    x, y = wcs.world_to_pixel(SkyCoord(ra*u.deg, dec*u.deg))
    fits_height, fits_width = data.shape
    y *= (png_width / fits_width)
    x *= (png_height / fits_height)

    fig = go.Figure()

    # Add the image as a background layer
    fig.add_layout_image(
        dict(
            source=png_path,
            xref="x",
            yref="y",
            x=0,
            y=png_height,  # y=height at top
            sizex=png_width,
            sizey=png_height,
            sizing="stretch",
            layer="below"
        )
    )
    # Define x and y axes to match the image size and orientation
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            visible=False,
            range=[0, png_width],
            constrain="domain"
        ),
        yaxis=dict(
            visible=False,
            range=[0, png_height],
            scaleanchor="x"
        ),
        clickmode='event+select'  # 👈 This is important
    )

    # Flip y for correct overlay
    y_plot = y

    # Add catalog points
    fig.add_trace(go.Scattergl(
        x=x,
        y=y_plot,
        mode="markers",
        marker=dict(
            size=15,
            color=catalog_df[color_by],  # Optional: color by redshift or other column
            colorscale="Inferno",
            colorbar=dict(
                len=0.5,  # height as a fraction of plot (e.g., 50%)
                y=0.5,  # vertical position of center (0 = bottom, 1 = top)
                thickness=15  # optional: control width
            ),
            showscale=True
        ),
        text=catalog_df["source_name"],
        hoverinfo="text",
        customdata=catalog_df["source_name"]  # 💡 send this to clickData
    ))

    return fig
