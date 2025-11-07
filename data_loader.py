import numpy as np
import pandas as pd
import os
import re
from functools import lru_cache

from config import FILE_PREFIX

def join_avoiding_duplicates(df1, df2, key, how='inner'):
    """
    Join two DataFrames on a given key without duplicating column names.

    Parameters:
    - df1, df2: DataFrames to join
    - key: column name or list of column names to join on
    - how: type of join ('inner', 'left', 'right', 'outer')

    Returns:
    - A merged DataFrame
    """
    if isinstance(key, str):
        key = [key]

    # Columns from df2 to include (exclude keys and duplicates)
    columns_to_use = [col for col in df2.columns if col not in key and col not in df1.columns]

    return df1.merge(df2[key + columns_to_use], on=key, how=how)

@lru_cache(maxsize=1)
def load_combined_catalog():
    params = pd.read_csv(FILE_PREFIX+"assets/all_spt3g_sources_in_spire_field_20250519_no_NaNs.csv")
    mbb = pd.read_csv(FILE_PREFIX+"assets/all_spt3g_sources_in_spire_field_20250519_no_NaNs_mbb_fit_params.csv")
    return join_avoiding_duplicates(params, mbb, "source_name")

@lru_cache(maxsize=1)
def get_redshift_dict():
    df = load_combined_catalog()
    return {row["source_name"]: row["z"] for _, row in df.iterrows()}

def get_source_name(filename):
    return re.split(r"_[^_]+\.png$", filename)[0]

@lru_cache(maxsize=None)
def get_sorted_images(image_dir):
    redshift_dict = get_redshift_dict()
    image_files = [
        f for f in os.listdir(image_dir)
        if f.endswith(".png") and get_source_name(f) in redshift_dict
    ]
    return sorted(image_files, key=get_source_name)

def prepare_table_data(notes):
    df = load_combined_catalog()
    df = df[["source_name", "z", "spt3g_ra(deg)", "spt3g_dec(deg)", "spt3g_s220(mjy)", "spt3g_s150(mjy)",
             "spt3g_alpha90", "spt3g_alpha220"]].copy()
    df["z"] = df["z"].round(4)
    df["spt3g_ra(deg)"] = df["spt3g_ra(deg)"].round(6)
    df["spt3g_dec(deg)"] = df["spt3g_dec(deg)"].round(6)
    df["spt3g_s220(mjy)"] = df["spt3g_s220(mjy)"].round(2)
    df["spt3g_s150(mjy)"] = df["spt3g_s150(mjy)"].round(2)
    df["spt3g_alpha90"] = df["spt3g_alpha90"].round(2)
    df["spt3g_alpha220"] = df["spt3g_alpha220"].round(2)
    df["has_note"] = np.array(df["source_name"].isin(notes.keys()), dtype=int)
    return df

def get_table_styles(theme):
    if theme == "dark":
        return {
            "style_cell": {
                "textAlign": "left",
                "padding": "5px",
                "maxWidth": "80%",
                "whiteSpace": "normal",
                "fontFamily": "Montserrat, sans-serif",
                "color": "#ffffff",
                "backgroundColor": "#000000"
            },
            "style_header": {"fontWeight": "bold", "backgroundColor": "#111111", "color": "#00FFAA"}
        }
    else:
        return {
            "style_cell": {
                "textAlign": "left",
                "padding": "5px",
                "maxWidth": "80%",
                "whiteSpace": "normal",
                "fontFamily": "Montserrat, sans-serif",
                "color": "#000000",
                "backgroundColor": "#ffffff"
            },
            "style_header": {"fontWeight": "bold", "backgroundColor": "#dddddd", "color": "#1e1e1e"}
        }
