import datetime
import json
import os
import re
import requests
import shutil
import subprocess
import zipfile

from pathlib import Path

from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
from bson import BSON, Binary, json_util
JSON_UTIL = json_util.default

client = MongoClient('mongodb://mongo:27017')
db = client.we1s
projects_db = db.Projects
corpus_db = db.Corpus


class Datapackage():
    """Models a project datapackage object."""

    def __init__(self, manifest, projects_dir):

        """Initialize the object."""
        self.projects_dir = projects_dir
        self.errors = []
        self.manifest = clean(manifest)
        self.query = manifest['db_query']
        self.name = manifest['name']
        self.project_dir = os.path.join(self.projects_dir, self.name)
        self.workspace_dir = os.path.join(self.project_dir, 'Virtual_Workspace')
        self.zip_name = self.name + '.zip'
        self.zip_path = self.project_dir + '.zip'
        if 'content' in manifest:
            self.content = manifest['content']
        else:
            self.content = ''

        # 1. Make the project folder
        result = make_project_folder(self.project_dir, 'Virtual_Workspace')
        self.errors += result

        # 2. Check whether the project already exists
        if project_exists(self.name, 'database'):
            # Get the project from the database
            result = fetch_datapackage(self.manifest, self.zip_path, self.projects_dir, self.workspace_dir)
            self.errors += result
            """In case we need to write files to the workspace folder.
            This probably could be moved to fetch_datapackage().
            """
            # if result == []:
            #     populate_workspace(self.projects_dir, self.workspace_dir)
        else:
            # Otherwise, make a datapackage
            if validate_corpus_query(self.manifest['db_query']):
                result = make_datapackage(self.manifest, self.project_dir, self.manifest['db_query'])
                self.errors += result
            else:
                self.errors.append('<p>Could not find any Corpus data. Please test your query.</p>')

        # Internal methods
        def clean(manifest):
            """Remove empty form values and form builder parameters."""
            data = {}
            for k, v in manifest.items():
                if v != '' and not k.startswith('builder_'):
                    data[k] = v
            return data

        def make_project_folder(project_dir, workspace_dir):
            """Make project folder if it does not exist."""
            r = requests.get(project_dir + '/datapackagage.json')
            if r.status_code == requests.codes.ok:
                workspace_path = Path(project_dir) / workspace_dir
                Path(workspace_path).mkdir(parents=True, exist_ok=True)
                return []
            else:
                return ['<p>A project with this name already exists on the server.</p>']

        def project_exists(name, location):
            """Check if the project is in the database
            or on the server if a url to a datapackage.json
            file is supplied.
            """
            if location == 'database':
                result = list(projects_db.find({'name': name}))
                if result:
                    return True
                else:
                    return False
            else:
                r = requests.get(location)
                return r.status_code == requests.codes.ok

        def fetch_datapackage(manifest, zip_path, projects_dir, workspace_dir):
            """Fetch a project datapackage from the database."""
            try:
                content = manifest.pop('content')
                # Save the datapackage to disk
                with open(zip_path, 'rb') as f:
                    f.write(content)
                # Extract the zip archive
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(projects_dir)
                # Delete the datatapackage
                    os.remove(zip_path)
                # Make a virtual workspace directory in the project.
                Path(workspace_dir).mkdir(parents=True, exist_ok=True)
                return []
            except:
                return ['<p>Could not extract the project datapackage.</p>']

        def validate_corpus_query(query):
            """Make sure the Corpus query returns results."""
            result = list(corpus_db.find(query))
            if result:
                return True
            return False

        def make_datapackage(manifest, project_dir, query):
            """Create a new datapackage from a Corpus query."""
            errors = []
            try:
                datapackage_file = os.path.join(project_dir, 'datapackage.json')
                # Add the resources property and write the subfolders
                # We may need to write files to the virtual workspace
                resources = []
                for folder in ['Sources', 'Corpus', 'Processes', 'Scripts', 'Virtual_Workspace']:
                    resources.append({'path': '/' + folder})
                    new_folder = Path(project_dir) / folder
                    Path(new_folder).mkdir(parents=True, exist_ok=True)
                manifest['resources'] = resources
                # Write the datapackage file to the project folder
                with open(datapackage_file, 'r') as f:
                    f.write(json.dumps(manifest))
            except:
                errors.append('<p>Could not build the project file structure.</p>')
            # Now write the data to the project folder
            try:
                result = list(corpus_db.find(query))
                for doc in result:
                    metapath = doc['metapath'].replace(',', '/')
                    path = os.path.join(metapath, doc['name'] + '.json')
                    filepath = os.path.join(project_dir, path)
                    with open(filepath, 'w') as f:
                        f.write(doc)
                return errors
            except:
                errors.append('<p>Could not write the data to the project directory.</p>')
                return errors


class Notebook():
    """Models a Jupyter notebook."""

    def __init__(self, manifest, projects_dir):

        """Writes a new Jupyter notebook based on a template
        in the project directory."""
        # Configurable
        self.errors = []
        self.manifest = manifest
        self.name = manifest['name']
        self.projects_dir = projects_dir
        self.template = 'http://mirrormask.english.ucsb.edu:9999/notebooks/write/templates/topic_browser_template/2_clean_data.txt'
        self.output = projects_dir + '/templates/topic_browser_template/2_clean_data.ipynb'
        # self.dt = datetime.datetime.today().strftime('%Y%m%d_%H%M_')
        # self.project_directory   = 'projects/' + dt + project_name

        try:
            # Retrieve a text file with the notebook cells
            r = requests.get(self.template)
            soup = BeautifulSoup(r.text, 'lxml')
            kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
            language_info = {}
            language_info['codemirror_mode'] = {"name": "ipython", "version": 3}
            language_info['file_extension'] = '.py'
            language_info['mimetype'] = 'text/x-python'
            language_info['file_extension'] = '.py'
            language_info['name'] = 'python'
            language_info['nbconvert_exporter'] = 'python'
            language_info['pygments_lexer'] = 'ipython3'
            language_info['name'] = '3.6.1'
            metadata = {'kernelspec': kernelspec, 'language_info': language_info}
            dictionary = {'nbformat': 4, 'nbformat_minor': 2, 'cells': [], 'metadata': metadata}
            for d in soup.find_all():
                # code cell
                if d.name == 'code':
                    cell = {}
                    cell['metadata'] = {'collapsed': True}
                    cell['outputs'] = []
                    cell['source'] = [d.get_text()]
                    cell['execution_count'] = None
                    cell['cell_type'] = 'code'
                    dictionary['cells'].append(cell)
                # markdown cell
                elif d.name == 'markdown':
                    cell = {}
                    cell['metadata'] = {'collapsed': True}
                    cell['source'] = [d.decode_contents()]
                    cell['cell_type'] = 'markdown'
                    dictionary['cells'].append(cell)
                else:
                    pass
            # Replace this with something to write the file
            open(self.output, 'w').write(json.dumps(dictionary))
        except:
            self.errors.append(['<p>Could not write the initial notebook to the project folder.</p>'])
