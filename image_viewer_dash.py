import os
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
from html_utils import theme_toggle_button
from config import (
    NOTES_FILE, MAP_FITS, MAP_PNG, COLOR_OPTIONS,
    TABLE_COLUMNS, USERS, SECRET_KEY, IS_LOCAL,
    FILE_PREFIX
)
from layouts import home_layout, viewer_layout, notes
from callbacks import register_callbacks

# === Flask + Flask-Login imports ===
from flask import Flask, redirect, url_for, request, abort, render_template_string
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)

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
    dcc.Store(id="res-mode-store", data="convolved", storage_type="session"),
    dcc.Store(id="filtered-data-store", data=[], storage_type="session"),
    dcc.Store(id="sorted-table-data", data=[], storage_type="session"),
    html.Div(id="cutout-placeholder", children=[]),
    html.Div(id="theme-wrapper", className="", children=[
        html.Div(id="page-content")])
])

register_callbacks(app, notes)

# === Routing Callback ===
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    State("theme-store", "data")
)
def display_page(pathname, stored_theme):
    theme = stored_theme or "dark"
    if pathname in ["/", "/home"]:
        return home_layout(theme)
    elif pathname.startswith("/viewer/"):
        source_name = unquote(pathname.split("/viewer/")[1])
        return viewer_layout(source_name)
    elif pathname == "/logout":
        return login()
    return html.Div("404 Page Not Found")


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
