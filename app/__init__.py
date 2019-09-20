"""Flask app init.py."""

# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

# import: standard
import json
import os
import re
import urllib
# import: third-party
from flask import Flask, render_template, request, url_for
import markdown
import pymongo
from pymongo import MongoClient

# import: app
from .database import DB

# Import constants
# import app.helpers.methods as methods

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
# Define the WSGI application object
app = Flask(__name__, instance_relative_config=True)

# Configurations that use app
# application = app  # our hosting requires application in passenger_wsgi

# Configurations
app.config.from_object('config')
app.config.from_pyfile('config.py')
# print(app.instance_path)
# print(app.config)

# Configure database
client = app.config['MONGO_CLIENT']
sources_db = app.config['SOURCES_DB']
corpus_db = app.config['CORPUS_DB']
projects_db = app.config['PROJECTS_DB']
db = DB(client, sources_db, corpus_db, projects_db)

# import app (must be after database is configured)
from .sources import sources  # nopep8 # pylint: disable=wrong-import-position
from .corpus import corpus  # nopep8 # pylint: disable=wrong-import-position
from .projects import projects  # nopep8 # pylint: disable=wrong-import-position
from .scripts import scripts  # nopep8 # pylint: disable=wrong-import-position
from .tasks import tasks  # nopep8 # pylint: disable=wrong-import-position


def register_blueprints(application):
    """Prevent circular imports."""
    application.register_blueprint(sources, url_prefix='/sources')
    application.register_blueprint(corpus, url_prefix='/corpus')
    application.register_blueprint(projects, url_prefix='/projects')
    application.register_blueprint(scripts, url_prefix='/scripts')
    application.register_blueprint(tasks, url_prefix='/tasks')


register_blueprints(app)

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/todo')
def todo():
    """Load To Do page."""
    return render_template('todo.html')


@app.route('/thought-experiments/<name>')
def thought_experiments(name):
    """Load Thought Experiments page."""
    filename = os.path.join('app/static/markdown', name + '.md')
    with open(filename, 'r') as f:
        md = f.read()
    html = markdown.markdown(md, ['markdown.extensions.extra'])
    return render_template('thought_experiments.html', html=html)


@app.route('/')
def home():
    """Load Home page."""
    return render_template('index.html')


@app.route('/guide')
def guide():
    """Load Guide page."""
    breadcrumbs = [{'link': '/guide', 'label': 'Guide'}]
    return render_template('guide.html', breadcrumbs=breadcrumbs)


def add_links(doc):
    """Add links to headers on /schema page."""
    pats = ['(<h1>)(.+?)(</h1>)', '(<h2>)(.+?)(</h2>)', '(<h3>)(.+?)(</h3>)', '(<h4>)(.+?)(</h4>)', '(<h5>)(.+?)(</h5>)']
    for p in pats:
        doc = re.sub(p, r'\g<1><a id="user-content-\g<2>" class="anchor" aria-hidden="true" href="#\g<2>"></a>\g<2>\g<3>', doc)
    return doc


@app.route('/schema')
def schema():
    """Load Schema page."""
    breadcrumbs = [{'link': '/schema', 'label': 'Manifest Schema Documentation'}]
    f = urllib.request.urlopen('https://github.com/whatevery1says/manifest/raw/master/we1s-manifest-schema-2.0.md')
    md = f.read().decode('utf-8')
    html = markdown.markdown(md, ['markdown.extensions.extra'])
    html = html.replace('<h1>WhatEvery1Says Schema</h1>', '')
    html = add_links(html)
    # Need to inject internal links in contents and elsewhere, as they are not
    # carried over from GitHub.
    return render_template('schema.html', html=html, breadcrumbs=breadcrumbs)


# Error handlers.

@app.errorhandler(500)
def internal_error(error):
    """Load 500 Error page."""
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    """Load 404 Error page."""
    return render_template('errors/404.html'), 404


@app.template_filter('is_list')
def is_list(value):
    """
    Jinja filter to to detect a list.

    Usage: `{% if var|is_list %}`
    """
    return isinstance(value, list)


# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#
# Default port:
if __name__ == '__main__':
    app.run()
# Or specify port manually:
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)
