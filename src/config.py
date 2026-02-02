import os

NOTES_FILE = os.getenv('SPT3G_VIEWER_NOTES_FILE', "notes.json")

USERNAME = os.getenv('SPT3G_VIEWER_USERNAME', "username")
PASSWORD = os.getenv('SPT3G_VIEWER_PASSWORD', "password")
USERS = {USERNAME: {"password": PASSWORD}}
SECRET_KEY = os.getenv('SPT3G_VIEWER_SECRET_KEY', "super-secret-change-me")

DEBUG_ENABLED = os.getenv('SPT3G_VIEWER_DEBUG_ENABLED', 'false').lower() == 'true'
URL_BASE_PATHNAME = os.getenv('SPT3G_VIEWER_URL_BASE_PATHNAME', "/")
SERVER_HOST = os.getenv('SPT3G_VIEWER_SERVER_HOST', "0.0.0.0")
SERVER_PORT = int(os.getenv('SPT3G_VIEWER_SERVER_PORT', '8000'))

FILE_PREFIX = os.getenv('SPT3G_VIEWER_URL_FILE_PREFIX', "")

# === Constants ===
MAP_FITS = FILE_PREFIX + "assets/spt2_itermap_20120621_PLW.fits"
MAP_PNG = FILE_PREFIX + "assets/spt2_itermap_20120621_PLW.jpg"

COLOR_OPTIONS = [
    {"label": "Phot-z", "value": "z"},
    {"label": "S(220GHz)", "value": "spt3g_s220(mjy)"},
    {"label": "S(150GHz)", "value": "spt3g_s150(mjy)"},
    {"label": "alpha90", "value": "spt3g_alpha90"},
    {"label": "alpha220", "value": "spt3g_alpha220"}
]

TABLE_COLUMNS = [
    {"name": "SPT3G source name", "id": "source_name"},
    {"name": "Phot-z", "id": "z"},
    {"name": "RA", "id": "spt3g_ra(deg)"},
    {"name": "Dec", "id": "spt3g_dec(deg)"},
    {"name": "S(220GHz)", "id": "spt3g_s220(mjy)"},
    {"name": "S(150GHz)", "id": "spt3g_s150(mjy)"},
    {"name": "alpha90", "id": "spt3g_alpha90"},
    {"name": "alpha220", "id": "spt3g_alpha220"},
    {"name": "Note?", "id": "has_note"},
]

TOGGLE_BANDS = ["mk", "spire250", "spire350", "spire500"]
