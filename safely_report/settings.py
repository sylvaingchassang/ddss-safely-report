from dotenv import load_dotenv

from safely_report.utils import get_env_var

# Load environment variables
load_dotenv()

# Configure security
SECRET_KEY = get_env_var("SAFELY_REPORT_SECRET_KEY")
ADMIN_PASSWORD = get_env_var("SAFELY_REPORT_ADMIN_PASSWORD")

# Configure server-side session
SESSION_TYPE = "filesystem"
SESSION_FILE_DIR = ".flask_sessions"
SESSION_USE_SIGNER = True

# Make each session expire after 12 hours of inactivity
SESSION_PERMANENT = True
SESSION_REFRESH_EACH_REQUEST = True
PERMANENT_SESSION_LIFETIME = 12 * 60 * 60  # In seconds

# Configure database
SQLALCHEMY_DATABASE_URI = get_env_var("SAFELY_REPORT_DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configure survey
XLSFORM_PATH = get_env_var("XLSFORM_PATH")
RESPONDENT_ROSTER_PATH = get_env_var("RESPONDENT_ROSTER_PATH")
ENUMERATOR_ROSTER_PATH = get_env_var("ENUMERATOR_ROSTER_PATH")
MEDIA_PATH = get_env_var("MEDIA_PATH")
