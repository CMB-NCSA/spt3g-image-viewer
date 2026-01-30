import os
import json
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

from html_utils import cutout_row, theme_toggle_button
from data_loader import prepare_table_data, get_table_styles
from interactive_map import create_map_figure
from config import FILE_PREFIX, MAP_FITS, MAP_PNG, TABLE_COLUMNS, COLOR_OPTIONS, NOTES_FILE

# === Notes ===
notes = json.load(open(NOTES_FILE)) if os.path.exists(NOTES_FILE) else {}

header_text = 'This table contains a list of all SPT3G SMGs in the 100 sq. deg. SSDF field. Click on a ' \
              'row in the table to view SPT3G, SPIRE and MeerKAT thumbnails and MBB fits for that source. ' \
              'Alternatively, you can click on the source in the SPIRE map on the right. The table can be ' \
              'filtered using the sliders below, or you can search for a source by name.'


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
        html.H3(
            header_text,
            style={
                "textAlign": "center",
                "marginTop": "20px",
                "marginBottom": "20px",
                "width": "50%",
                "marginLeft": "auto",
                "marginRight": "auto",
                "line-height": "1.4"
            }
        ),

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
                    max=26.0,
                    step=0.05,
                    value=[1.0, 26.0],
                    marks={i: str(i) for i in range(0, 27) if i % 3 == 0},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            html.Div([
                html.Label("Filter by S(150GHz):"),
                dcc.RangeSlider(
                    id="s150-slider",
                    min=0.0,
                    max=6.0,
                    step=0.05,
                    value=[0.0, 6.0],
                    marks={i: str(i) for i in range(0, 7)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),

            # spectral index filter bars
            html.Div([
                html.Label("Filter by alpha90:"),
                dcc.RangeSlider(
                    id="a90-slider",
                    min=0.0,
                    max=5.0,
                    step=0.05,
                    value=[0.0, 5.0],
                    marks={i: str(i) for i in range(0, 9)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False
                )
            ], style={"flex": "1", "marginRight": "20px"}),
            html.Div([
                html.Label("Filter by alpha220:"),
                dcc.RangeSlider(
                    id="a220-slider",
                    min=0.0,
                    max=5.0,
                    step=0.05,
                    value=[0.0, 5.0],
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
        html.Div(id="debug-output", style={"color": "yellow", "textAlign": "center"}),

        html.Div(
            dbc.RadioItems(
                id="res-mode",
                options=[
                    {"label": "Native", "value": "native"},
                    {"label": "SPT-Convolved", "value": "convolved"},
                ],
                value="convolved",
                inline=True,
                style={"fontSize": "18px"},
                labelStyle={
                    "display": "inline-block",
                    "padding": "15px 40px",
                    "margin": "0 10px",
                    "cursor": "pointer",
                    "fontWeight": "bold"
                },
                input_class_name="btn-check",
                label_class_name="btn btn-info"
            ),
            style={"textAlign": "center", "marginBottom": "20px"}
        ),

        cutout_row([
            {"prefix": "mk", "mode": "native", "suffix": "overlay", "title": "MeerKAT", "folder": "mk"},
            {"prefix": "spt3g220", "mode": "native", "suffix": "overlay", "title": "SPT3G 220GHz", "folder":
                "spt3g220"},
            {"prefix": "spt3g150", "mode": "native", "suffix": "overlay", "title": "SPT3G 150GHz", "folder":
                "spt3g150"},
            {"prefix": "spt3g90", "mode": "native", "suffix": "overlay", "title": "SPT3G 90GHz", "folder": "spt3g90"},
            {"prefix": "sed", "mode": ".", "folder": "best_fit_plots", "suffix": "best-fit", "title": "SED Fit"}
        ], source_name),

        html.Div([
            # Info box on the left
            html.Div([
                html.H4("Cutout Information", style={"marginBottom": "15px"}),
                html.P([
                    html.Strong("Contours: "),
                    "Radio contours from SPT3G 220GHz overlaid on all images."
                ], style={"marginBottom": "10px"}),
                html.P([
                    html.Strong("Resolution: "),
                    "Native shows original telescope resolution. SPT-Convolved shows all images convolved to SPT beam size (1'')."
                ], style={"marginBottom": "10px"}),
                html.P([
                    html.Strong("Modified Blackbody fits: "),
                    "SPIRE non-detections are all set to 10mJy upper limits. Corner plots show the posterior "
                    "distribution from MCMC fitting."
                ], style={"marginBottom": "10px"}),
            ], style={
                "width": "20%",
                "padding": "20px",
                "backgroundColor": "rgba(0, 123, 255, 0.1)",
                "borderRadius": "10px",
                "border": "2px solid #007bff",
                "marginRight": "2%",
                "height": "350px"
            }),

            # Cutouts on the right
            html.Div(
                cutout_row([
                    {"prefix": "spire500", "mode": "native", "suffix": "overlay", "title": "SPIRE 500μm",
                     "folder": "spire500"},
                    {"prefix": "spire350", "mode": "native", "suffix": "overlay", "title": "SPIRE 350μm",
                     "folder": "spire350"},
                    {"prefix": "spire250", "mode": "native", "suffix": "overlay", "title": "SPIRE 250μm",
                     "folder": "spire250"},
                    {"prefix": "corner", "mode": ".", "folder": "corner_plots", "suffix": "corner",
                     "title": "Corner Plot"}
                ], source_name),
                style={"width": "100%"}
            )
        ], style={"display": "flex", "justifyContent": "flex-start", "marginBottom": "30px", "width": "100%"}),

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
