from dash import html

def cutout_row(images, source_name):
    return html.Div(
        [
            html.Figure([
                html.Img(
                    src=f"/assets/{folder}/{source_name}_{suffix}.png",
                    style={"width": "100%"},
                    id={"type": "thumbnail", "index": f"{prefix}_{source_name}"},
                    n_clicks=0
                ),
                html.Figcaption(title)
            ], style={"width": "15%", "textAlign": "center"})
            for prefix, folder, suffix, title in images
        ],
        style={"display": "flex", "gap": "2%", "justifyContent": "center", "marginBottom": "30px"}
    )

def theme_toggle_button():
    return html.Button(
        "Toggle Light/Dark Mode",
        id="theme-button",
        n_clicks=0,
        # **{"aria-label": "Change theme"},
        style={"padding": "10px 20px", "margin": "20px"}
    )
