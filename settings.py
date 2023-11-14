from os import environ

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure security
SECRET_KEY = environ.get(
    "SECRET_KEY",
    "examplesecret",  # Default
)

# Configure server-side session
SESSION_TYPE = "filesystem"
SESSION_FILE_DIR = ".flask_sessions"
SESSION_USE_SIGNER = True
SESSION_PERMANENT = False

# Configure database
SQLALCHEMY_DATABASE_URI = environ.get(
    "SQLALCHEMY_DATABASE_URI",
    "sqlite:///db.sqlite",  # Default
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configure survey
XLSFORM_PATH = environ.get(
    "XLSFORM_PATH",
    "./tests/data/stats4sd_example_xlsform_adapted.xlsx",  # Default
)
