from dash import html

def cutout_row(images, source_name, mode="native", row_style=None):
    """
    images: list of dicts, each dict defines one panel.
            Required keys:
                prefix, folder, suffix, title
            Optional keys:
                img_style, fig_style, caption_style, width
    """

    default_row_style = {
        "display": "flex",
        "gap": "2%",
        "justifyContent": "flex-start",
        "marginBottom": "30px"
    }

    row_style = {**default_row_style, **(row_style or {})}

    figures = []
    for img in images:
        prefix   = img["prefix"]
        folder   = img["folder"]
        suffix   = img["suffix"]
        title    = img["title"]


        # Optional overrides
        width          = img.get("width", f"{100/len(images)}%")
        fig_style      = img.get("fig_style", {"width": width, "textAlign": "center"})
        img_style      = img.get("img_style", {"width": "100%"})
        caption_style  = img.get("caption_style", {"fontSize": "25px"})

        figures.append(
            html.Figure(
                [
                    html.Img(
                        src=f"/assets/{mode}/{folder}/{source_name}_{suffix}.png",
                        style=img_style,
                        id={"type": "cutout_img", "index": f"{prefix}_{source_name}", "band": prefix,
                            "folder": folder, "suffix": suffix},
                        n_clicks=0
                    ),
                    html.Figcaption(title, style=caption_style)
                ],
                style=fig_style
            )
        )

    return html.Div(figures, style=row_style)

def theme_toggle_button():
    return html.Button(
        "Toggle Light/Dark Mode",
        id="theme-button",
        n_clicks=0,
        # **{"aria-label": "Change theme"},
        style={"padding": "10px 20px", "margin": "20px"}
    )
