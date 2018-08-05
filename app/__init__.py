"""Flask app init.py
"""

# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import os
import re
import urllib

import markdown

from flask import Flask, render_template, request

from .sources import sources
from .corpus import corpus
from .projects import projects
from .scripts import scripts
from .tasks import tasks

# Import constants
# import app.helpers.methods as methods

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
# Define the WSGI application object
app = Flask(__name__, instance_relative_config=True)

# Configurations that use app
# application = app  # our hosting requires application in passenger_wsgi

app.register_blueprint(sources, url_prefix='/sources')
app.register_blueprint(corpus, url_prefix='/corpus')
app.register_blueprint(projects, url_prefix='/projects')
app.register_blueprint(scripts, url_prefix='/scripts')
app.register_blueprint(tasks, url_prefix='/tasks')

# Configurations
app.config.from_object('config')
app.config.from_pyfile('config.py')
# print(app.instance_path)

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/todo')
def todo():
    return render_template('todo.html')


@app.route('/thought-experiments/<name>')
def thought_experiments(name):
    filename = os.path.join('app/static/markdown', name + '.md')
    with open(filename, 'r') as f:
        md = f.read()
    html = markdown.markdown(md, ['markdown.extensions.extra'])
    return render_template('thought_experiments.html', html=html)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/guide')
def guide():
    breadcrumbs = [{'link': '/guide', 'label': 'Guide'}]
    return render_template('guide.html', breadcrumbs=breadcrumbs)


def add_links(doc):
    """ Helper for /schema """
    import re
    pats = ['(<h1>)(.+?)(</h1>)', '(<h2>)(.+?)(</h2>)', '(<h3>)(.+?)(</h3>)', '(<h4>)(.+?)(</h4>)', '(<h5>)(.+?)(</h5>)']
    for p in pats:
        doc = re.sub(p, '\g<1><a id="user-content-\g<2>" class="anchor" aria-hidden="true" href="#\g<2>"></a>\g<2>\g<3>', doc)
    return doc


@app.route('/schema')
def schema():
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
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#
# Default port:
if __name__ == '__main__':
    app.run()
# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
