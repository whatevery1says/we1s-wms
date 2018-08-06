"""config.py: Flask site configuration file"""

UPLOAD_FOLDER = 'uploads'
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'md', 'docx', 'jpg', 'xlsx'}
ALLOWED_EXTENSIONS = {'csv', 'tsv', 'xls', 'xlsx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"


class BaseConfig:
    """Base configuration: localisation (language and timezone options)"""
    SUPPORTED_LANGUAGES = {'en': 'English', 'fr': 'Francais'}
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
