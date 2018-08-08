"""Scripts methods.py.

Note: This module has not yet been developed. This file is a placeholder.
"""

# import: standard
# import: third-party
from flask import current_app
from pymongo import MongoClient
# import: app


# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
corpus_db = db.Corpus
scripts_db = db.Scripts

# ----------------------------------------------------------------------------#
# General Helper Functions
# ----------------------------------------------------------------------------#


def allowed_file(filename):
    """Test whether a filename contains an allowed extension.

    Returns a Boolean.
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']
