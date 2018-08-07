"""Scripts methods.py.
Note: This module has not yet been developed. This file is a placeholder.
"""

import itertools
import json
import os
import re
import requests
import shutil
import zipfile

import dateutil.parser
from datetime import datetime

import tabulator
from tabulator import Stream

from flask import current_app
from jsonschema import validate, FormatChecker
import pandas as pd
from tableschema_pandas import Storage

import pymongo
from pymongo import MongoClient

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
