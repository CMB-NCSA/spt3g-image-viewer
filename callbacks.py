from dash import Input, Output, State, ALL, no_update, callback_context
import dash
import json
from dash.exceptions import PreventUpdate
from urllib.parse import unquote
from interactive_map import create_map_figure
from data_loader import prepare_table_data, get_table_styles
from config import MAP_FITS, MAP_PNG, NOTES_FILE, TOGGLE_BANDS
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def register_callbacks(app, notes):
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
        if n_clicks == 0 or n_clicks == prev_clicks:
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

    # Store the resolution mode when toggled
    @app.callback(
        Output("res-mode-store", "data"),
        Input("res-mode", "value"),
        prevent_initial_call=True
    )
    def store_res_mode(value):
        return value

    # Clientside callback to update image sources
    app.clientside_callback(
        """
        function(resMode) {
            // Find all cutout images
            const images = document.querySelectorAll('img[id*="cutout_img"]');
            console.log('Found ' + images.length + ' cutout images');

            images.forEach(img => {
                try {
                    const id = JSON.parse(img.id);
                    if (id.type === 'cutout_img') {
                        const folder = id.folder;
                        const suffix = id.suffix;
                        const sourceName = id.index.split('_').slice(1).join('_');
                        const newSrc = `/assets/${resMode}/${folder}/${sourceName}_${suffix}.png`;
                        console.log('Updating:', img.src, '->', newSrc);
                        img.src = newSrc;
                    }
                } catch(e) {
                    console.error('Error updating image:', e);
                }
            });
            return window.dash_clientside.no_update;
        }
        """,
        Output("debug-output", "children"),
        Input("res-mode-store", "data")
    )