"""Tasks __init__.py."""

# import: standard
from datetime import datetime
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
# import: third-party
from bson import BSON, Binary, json_util
from flask import Blueprint, render_template, request, url_for, current_app, send_file
from jsonschema import validate, FormatChecker
import pymongo
from pymongo import MongoClient
import requests
import tabulator
from werkzeug.utils import secure_filename
# import: app


JSON_UTIL = json_util.default

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
projects_db = db.Projects
corpus_db = db.Corpus

tasks = Blueprint('tasks', __name__, template_folder='tasks')

# from app.tasks.helpers import methods as methods

# ----------------------------------------------------------------------------#
# Constants.
# ----------------------------------------------------------------------------#


ALLOWED_EXTENSIONS = ['zip']

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@tasks.route('/')
def index():
    """Tasks index page."""
    scripts = ['js/tasks/tasks.js']  # E.g. ['js/tasks/tasks.js']
    styles = []  # E.g. ['css/tasks/tasks.css']
    breadcrumbs = [{'link': '/tasks', 'label': 'Manage Tasks'}]
    task_list = [{'task_name': 'A collection',
                  'task_id': '123',
                  'task_result': 'QUEUED',
                  'task_status': 3},
                 {'task_name': 'Another collection',
                  'task_id': '456',
                  'task_result': 'QUEUED',
                  'task_status': 3}]
    return render_template('tasks/index.html', scripts=scripts, styles=styles,
                           breadcrumbs=breadcrumbs, tasks=task_list)


@tasks.route('/api/status/<id>', methods=['GET', 'POST'])
def api_status(job_id):
    """For testing."""
    response = json.dumps({'success': True,
                           'id': '123',
                           'status': 1,
                           'result': 'STARTED'})
    return response


@tasks.route('/api/enqueue', methods=['GET', 'POST'])
def api_enqueue():
    """For testing."""
    response = json.dumps({
        'success': True,
        'id': '789',
        'status': 3,
        'result': 'QUEUED'})
    return response
