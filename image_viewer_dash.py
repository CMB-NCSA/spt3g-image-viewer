import os
import json
import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
from urllib.parse import unquote
from data_loader import (
    get_sorted_images,
    get_source_name,
    prepare_table_data,
    load_combined_catalog,
    get_table_styles
)
from interactive_map import create_map_figure
from html_utils import cutout_row, theme_toggle_button
from config import (
    NOTES_FILE, MAP_FITS, MAP_PNG, COLOR_OPTIONS,
    TABLE_COLUMNS, USERS, SECRET_KEY, IS_LOCAL,
    FILE_PREFIX
)

# === Flask + Flask-Login imports ===
from flask import Flask, redirect, url_for, request, abort, render_template_string
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)

# === Notes ===
notes = json.load(open(NOTES_FILE)) if os.path.exists(NOTES_FILE) else {}

# -----------------------------------------------------------------------------
# Flask + Login setup
# -----------------------------------------------------------------------------
server = Flask(__name__)
server.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(server)


class User(UserMixin):
    def __init__(self, id):
        self.id = id

@server.before_request
def block_direct_access():
    if not IS_LOCAL:
        if request.headers.get("X-Forwarded-By") != "CloudFront":
            abort(403)


@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))


with open("login_template.html") as f:
    login_html = f.read()

@server.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username]["password"] == password:
            login_user(User(username))
            return redirect("/")
        return "Invalid credentials", 401

    return render_template_string(login_html)


@server.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


# === App Initialization ===
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.SANDSTONE],
                assets_folder=FILE_PREFIX + "assets", suppress_callback_exceptions=True)

# === App Layout ===
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="theme-store", storage_type="local"),
    dcc.Store(id="theme-clicks", data=0),
    dcc.Store(id="filtered-data-store", data=[], storage_type="session"),
    dcc.Store(id="sorted-table-data", data=[], storage_type="session"),
    html.Div(id="theme-wrapper", className="", children=[
        html.Div(id="page-content")])
])

header_text = 'This table contains a list of all 1110 SMGs located within the 100 sq. deg. SSDF field. Click on a ' \
              'source to view thumbnails and SED fits. The table can be ordered by any column simply by clicking on ' \
              'the column header.'


# === Home Page Layout ===
def home_layout(theme="dark"):
    # prepare the dataframe used in the table
    table_df = prepare_table_data(notes)
    # prepare the map figure used on the right-hand side of the page
    map_fig = create_map_figure(
        catalog_path=FILE_PREFIX + "assets/all_spt3g_sources_in_spire_field_20250519_no_NaNs_combined.csv",
        catalog_df=None,
        fits_path=MAP_FITS,
        png_path="/assets/spt2_itermap_20120621_PLW.jpg",
        png_path_local=MAP_PNG
    )

    initial_table_styles = get_table_styles(theme)

    # return the HTML layout
    return html.Div([
        # Headers
        html.H1("SPT3G Source Catalog", style={"textAlign": "center", "marginTop": "20px", "marginBottom": "20px"}),
        html.H3(header_text, style={"textAlign": "center", "marginTop": "20px", "marginBottom": "20px"}),

        # Search bar
        html.Div([
            html.Div([
                html.Label("Filter by Source Name:"),
                dcc.Input(
                    id="search-input",
                    type="text",
                    placeholder="e.g., SPT3G...",
                    debounce=True,  # triggers callback only when typing stops
                    style={"width": "90%", "padding": "15px", "margin": "20px"}
                )
            ], style={"flex": "1", "marginRight": "2px"}),

            html.Div(
                [dbc.Button("Logout", color="danger", href="/logout", external_link=True)],
                style={"display": "flex", "alignItems": "center"}
            ),
            html.Div([
                theme_toggle_button()
            ], style={"display": "flex", "alignItems": "center"}),  # Aligns button to bottom of slider
        ], style={"display": "flex", "width": "95%", "margin": "20px"}),

        html.Div([
            # Photometric redshift filter bar
            html.Div([
                html.Label("Filter by Photometric Redshift:"),
                dcc.RangeSlider(
                    id="redshift-slider",
                    min=0.0,
                    max=8.0,
                    step=0.1,
                    value=[0.0, 8.0],
                    marks={i: str(i) for i in range(0, 9)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            html.Div([
                html.Label("Filter by S(220GHz):"),
                dcc.RangeSlider(
                    id="s220-slider",
                    min=1.0,
                    max=8.0,
                    step=0.05,
                    value=[1.0, 8.0],
                    marks={i: str(i) for i in range(0, 9)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            html.Div([
                html.Label("Filter by S(150GHz):"),
                dcc.RangeSlider(
                    id="s150-slider",
                    min=0.0,
                    max=3.0,
                    step=0.05,
                    value=[0.0, 3.0],
                    marks={i: str(i) for i in range(0, 9)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),

            # spectral index filter bars
            html.Div([
                html.Label("Filter by alpha90:"),
                dcc.RangeSlider(
                    id="a90-slider",
                    min=1.0,
                    max=4.5,
                    step=0.05,
                    value=[1.0, 4.5],
                    marks={i: str(i) for i in range(0, 9)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            html.Div([
                html.Label("Filter by alpha220:"),
                dcc.RangeSlider(
                    id="a220-slider",
                    min=0.5,
                    max=3.0,
                    step=0.05,
                    value=[0.5, 3.0],
                    marks={i: str(i) for i in range(0, 9)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}), ], style={"display": "flex", "width": "95%",
                                                                      "margin": "20px"}),

        html.Div(
            id="result-count",
            style={
                "marginBottom": "10px",
                "fontWeight": "bold",
                "fontSize": "20px",
                "color": "#00FFAA",
                "fontFamily": "Montserrat, sans-serif",
                "transition": "all 0.3s ease"
            }
        ),

        html.Div([
            # Left column: Data table
            html.Div(
                dash_table.DataTable(
                    id='catalog-table',
                    columns=TABLE_COLUMNS,
                    data=table_df.to_dict("records"),
                    style_table={"overflowY": "scroll", "maxHeight": "80vh"},
                    style_cell=initial_table_styles["style_cell"],
                    style_header=initial_table_styles["style_header"],
                    style_data_conditional=[
                        {
                            "if": {"filter_query": "{has_note} = 1"},
                            "fontWeight": "bold",
                        }
                    ],
                    sort_action='custom',
                    sort_mode='single',
                    row_selectable='single'
                ),
            style={"width": "80%", "paddingRight": "2%"}
            ),

            # Right column: Map
            html.Div([
                html.Div([
                    html.Label("Color points by:"),
                    dcc.Dropdown(
                        id="color-variable-dropdown",
                        options=COLOR_OPTIONS,
                        value="z",  # default
                        clearable=False,
                        style={"width": "80%"}
                    )
                ], style={"marginBottom": "10px"}),
                dcc.Loading(
                    id="map-loading",
                    type="circle",
                    children=dcc.Graph(
                        id="graph-id",
                        figure=map_fig,
                        config={"scrollZoom": True},
                        style={"height": "50vh", "png_width": "100%"},
                        clear_on_unhover=True
                    )
                )
            ],
                style={"width": "30%", "position": "sticky", "top": "20px"}
            )
        ], style={"display": "flex", "justifyContent": "space-between", "margin": "0 5%"})
    ])


# === Viewer Layout ===
def viewer_layout(source_name):
    note = notes.get(source_name, "")

    return dbc.Container([
        html.H1(f"{source_name} cutouts", style={"textAlign": "center", "marginBottom": "30px"}),

        cutout_row([
            ("mk", "mk_cutouts_spt3g_contours", "overlay", "MeerKAT"),
            ("spt3g220", "spt3g220_cutouts_spt3g_contours", "overlay", "SPT3G 220GHz"),
            ("spt3g150", "spt3g150_cutouts_spt3g_contours", "overlay", "SPT3G 150GHz"),
            ("spt3g90", "spt3g90_cutouts_spt3g_contours", "overlay", "SPT3G 90GHz"),
            ("sed", "best_fit_plots", "best-fit", "SED Fit")
        ], source_name),

        cutout_row([
            ("spire500", "spire500_cutouts_spt3g_contours", "overlay", "SPIRE 500μm"),
            ("spire350", "spire350_cutouts_spt3g_contours", "overlay", "SPIRE 350μm"),
            ("spire250", "spire250_cutouts_spt3g_contours", "overlay", "SPIRE 250μm"),
            ("corner", "corner_plots", "corner", "Corner Plot")
        ], source_name),

        dcc.Textarea(
            id="notes-text",
            value=note,
            placeholder="Enter your notes for this image...",
            style={
                "width": "75%",
                "height": 150,
                "borderRadius": "10px",
                "padding": "10px",
                "fontSize": "16px",
                "margin": "0 auto",
                "display": "block"
            }
        ),

        html.Div([
            # theme_toggle_button(),
            html.Button(
                "Save Notes",
                id="save-button",
                n_clicks=0,
                style={"padding": "10px 20px", "margin": "20px"}
            ),
            # html.Div("Use ← and → keys to navigate between sources.",
            #          style={"textAlign": "center", "color": "gray", "marginTop": "10px"}),            # html.Div("Use ← and → keys to navigate between sources.",
            #          style={"textAlign": "center", "color": "gray", "marginTop": "10px"}),
            html.Div([
                dbc.Button("◀️ Previous", id="prev-button", color="info", style={"margin": "10px"}),
                dcc.Link(dbc.Button("Back to Home", color="secondary", style={"margin": "10px"}), href="/"),
                dbc.Button("▶️ Next", id="next-button", color="info", style={"margin": "10px"})
            ], style={"textAlign": "center"})

        ], style={"marginTop": "20px", "textAlign": "center"}),

        html.Div(id="save-status", style={"textAlign": "center", "marginTop": "10px", "color": "green"}),
        dcc.Store(id="current-source", data=source_name),
        dcc.Store(id="last-nav-click", data=None),

        html.Div(
            id="lightbox-overlay",
            children=[
                html.Img(id="lightbox-image", className="enlarged-image"),
                html.Button("Close", id="close-lightbox", style={"margin": "20px", "font-size": "50px"})
            ]
        ),
        dcc.Store(id="selected-image-src")
    ], fluid=True)


# === Routing Callback ===
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    State("theme-store", "data")
)
def display_page(pathname, stored_theme):
    theme = stored_theme or "dark"
    if pathname in ["/", "/home"]:
        print()
        print(theme.upper())
        print()
        return home_layout(theme)
    elif pathname.startswith("/viewer/"):
        print()
        print(theme.upper())
        print()
        source_name = unquote(pathname.split("/viewer/")[1])
        return viewer_layout(source_name)
    elif pathname == "/logout":
        return login()
    return html.Div("404 Page Not Found")


# === Save Note Callback ===
@app.callback(
    Output("save-status", "children"),
    Input("save-button", "n_clicks"),
    State("notes-text", "value"),
    State("current-source", "data"),
    prevent_initial_call=True
)
def save_user_note(n_clicks, note_text, source_name):
    if source_name:
        notes[source_name] = note_text
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f, indent=2)
        return "✅ Notes saved!"
    return "⚠️ Could not save note."


# === Navigation to cutout page ===
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("catalog-table", "active_cell"),
    Input("graph-id", "clickData"),
    State("catalog-table", "data"),
    prevent_initial_call=True
)
def go_to_viewer(active_cell, clickData, visible_table_data):
    # --- If user clicks on a map point ---
    if clickData and "points" in clickData:
        try:
            source_name = clickData["points"][0]["customdata"]
            if isinstance(source_name, list):
                source_name = source_name[0]
            return f"/viewer/{source_name}"
        except Exception:
            pass

    # --- If user clicks on a table row ---
    if active_cell and visible_table_data:
        try:
            source_name = visible_table_data[active_cell["row"]]["source_name"]
            return f"/viewer/{source_name}"
        except Exception:
            pass

    return dash.no_update


# === Store last navigation button clicked ===
@app.callback(
    Output("last-nav-click", "data"),
    Input("next-button", "n_clicks"),
    Input("prev-button", "n_clicks"),
    prevent_initial_call=True
)
def store_last_click(next_clicks, prev_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    return trigger


# === Scroll Viewer Navigation Callback ===
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("selected-image-src", "data", allow_duplicate=True),
    Input("last-nav-click", "data"),
    State("current-source", "data"),
    State("sorted-table-data", "data"),
    prevent_initial_call=True
)
def scroll_sources(trigger_id, current_source, table_data):
    if not trigger_id or not table_data:
        raise dash.exceptions.PreventUpdate

    sources = [row["source_name"] for row in table_data]
    try:
        current_index = sources.index(current_source)
    except ValueError:
        current_index = 0

    if trigger_id == "next-button":
        new_index = (current_index + 1) % len(sources)
    elif trigger_id == "prev-button":
        new_index = (current_index - 1) % len(sources)
    else:
        raise dash.exceptions.PreventUpdate

    # Clear lightbox image when navigating
    return f"/viewer/{sources[new_index]}", None



# === Highlight selected source on the map and update color coding ===
@app.callback(
    Output("catalog-table", "data"),
    Output("result-count", "children"),
    Output("graph-id", "figure"),
    Output("sorted-table-data", "data"),
    Input("search-input", "value"),
    Input("redshift-slider", "value"),
    Input("s220-slider", "value"),
    Input("s150-slider", "value"),
    Input("a90-slider", "value"),
    Input("a220-slider", "value"),
    Input("color-variable-dropdown", "value"),
    Input("catalog-table", "selected_rows"),
    Input("catalog-table", "sort_by"),
)
def update_table_and_map(search_text, redshift_range, s220_range, s150_range, a90_range, a220_range,
                         color_by, selected_rows, sort_by):
    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd

    df = prepare_table_data(notes)

    # --- Apply search filter ---
    if search_text:
        search_text = search_text.lower()
        df = df[df["source_name"].str.lower().str.contains(search_text)]

    # --- Apply redshift filter ---
    if redshift_range:
        z_min, z_max = redshift_range
        df = df[df["z"].between(z_min, z_max)]

    # --- Apply S220 filter ---
    if s220_range:
        s220_min, s220_max = s220_range
        if "spt3g_s220(mjy)" in df.columns:
            df = df[df["spt3g_s220(mjy)"].between(s220_min, s220_max)]

    # --- Apply S150 filter ---
    if s150_range:
        s150_min, s150_max = s150_range
        if "spt3g_s150(mjy)" in df.columns:
            df = df[df["spt3g_s150(mjy)"].between(s150_min, s150_max)]

    # --- Apply A90 filter ---
    if a90_range:
        a90_min, a90_max = a90_range
        if "spt3g_alpha90" in df.columns:
            df = df[df["spt3g_alpha90"].between(a90_min, a90_max)]

    # --- Apply A220 filter ---
    if a220_range:
        a220_min, a220_max = a220_range
        if "spt3g_alpha220" in df.columns:
            df = df[df["spt3g_alpha220"].between(a220_min, a220_max)]

    # --- Apply sorting ---
    if sort_by:
        for sort in reversed(sort_by):
            df.sort_values(
                by=sort["column_id"],
                ascending=(sort["direction"] == "asc"),
                inplace=True
            )

    # --- Create map figure ---
    fig = create_map_figure(
        catalog_df=df,
        fits_path=MAP_FITS,
        png_path="/assets/spt2_itermap_20120621_PLW.jpg",
        png_path_local=MAP_PNG,
        color_by=color_by
    )

    # --- Highlight selected source ---
    if selected_rows:
        try:
            selected_source = df.iloc[selected_rows[0]]["source_name"]

            for trace in fig["data"]:
                if "customdata" in trace and selected_source in trace["customdata"]:
                    index = list(trace["customdata"]).index(selected_source)
                    fig.add_trace(go.Scattergl(
                        x=[trace["x"][index]],
                        y=[trace["y"][index]],
                        mode="markers",
                        marker=dict(
                            size=18,
                            color="white",
                            symbol="circle-open",
                            line=dict(width=5.5)
                        ),
                        showlegend=False
                    ))
                    break
        except Exception:
            pass

    return df.to_dict("records"), f"Showing {len(df)} result(s)", fig, df.to_dict("records")



# === Lightbox for enlarging selected image ===
@app.callback(
    Output("lightbox-overlay", "style"),
    Output("lightbox-image", "src"),
    Input("selected-image-src", "data"),
    Input("close-lightbox", "n_clicks"),
    prevent_initial_call=True
)
def display_lightbox(image_src, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "close-lightbox":
        return {"display": "none"}, None
    if image_src:
        return {
                   "display": "flex",
                   "position": "fixed",
                   "top": 0,
                   "left": 0,
                   "width": "100%",
                   "height": "100%",
                   "backgroundColor": "rgba(0, 0, 0, 0.8)",
                   "zIndex": 9999,
                   "justifyContent": "center",
                   "alignItems": "center"
               }, image_src
    return {"display": "none"}, None


# === Allow user to click on an image to enlarge it ===
@app.callback(
    Output("selected-image-src", "data"),
    Input({"type": "thumbnail", "index": ALL}, "n_clicks"),
    State({"type": "thumbnail", "index": ALL}, "src"),
    prevent_initial_call=True
)
def store_clicked_image(n_clicks_list, src_list):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    # Get the ID of the component that triggered the callback
    triggered_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
    index = triggered_id["index"]

    # Match the triggered index to the corresponding source
    for id_obj, src in zip(ctx.inputs_list[0], src_list):
        if id_obj["id"]["index"] == index:
            return src

    raise dash.exceptions.PreventUpdate


# === Theme updates
@app.callback(
    Output("theme-store", "data"),
    Output("theme-clicks", "data"),
    Input("theme-button", "n_clicks"),
    State("theme-clicks", "data"),
    State("theme-store", "data"),
    prevent_initial_call=True
)
def toggle_theme(n_clicks, prev_clicks, current_theme):
    if n_clicks==0 or n_clicks==prev_clicks:
        return current_theme, n_clicks
    else:
        return ("light" if current_theme == "dark" else "dark"), n_clicks


@app.callback(
    Output("theme-wrapper", "className"),
    Input("theme-store", "data")
)
def apply_theme_class(theme):
    return f"{theme}-mode" if theme else "dark-mode"


@app.callback(
    Output("catalog-table", "style_cell"),
    Output("catalog-table", "style_header"),
    Input("theme-store", "data"),
    Input("url", "pathname"),  # triggers on navigation
)
def update_table_theme(theme, _):
    styles = get_table_styles(theme)
    return styles["style_cell"], styles["style_header"]



# @app.callback(
#     Output("theme-store", "data", allow_duplicate=True),
#     Input("url", "pathname"),
#     State("theme-store", "data"),
#     prevent_initial_call=True
# )
# def persist_theme_on_navigation(_, stored_theme):
#     return stored_theme


# -----------------------------------------------------------------------------
# Protect Dash routes with login_required
# -----------------------------------------------------------------------------
url_base = app.config.get("url_base_pathname") or "/"

for view_func in list(app.server.view_functions):
    if view_func.startswith(url_base):
        app.server.view_functions[view_func] = login_required(app.server.view_functions[view_func])

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.run(
        debug=IS_LOCAL,
        host="127.0.0.1" if IS_LOCAL else "0.0.0.0",
        port=8050
    )
