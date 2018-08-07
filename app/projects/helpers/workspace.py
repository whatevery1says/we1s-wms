"""Projects workspace.py."""

import json
import os
import re
import requests
import shutil
import subprocess
import zipfile

from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
from bson import BSON, Binary, json_util
JSON_UTIL = json_util.default

client = MongoClient('mongodb://localhost:27017')
db = client.we1s
projects_db = db.Projects
corpus_db = db.Corpus


def clean(manifest):
    """Remove empty form values and form builder parameters."""
    data = {}
    for k, v in manifest.items():
        if v != '' and not k.startswith('builder_'):
            data[k] = v
    return data


def make_project_folder(project_dir, workspace_dir):
    """Make project folder if it does not exist."""
    if not os.path.isdir(project_dir):
        workspace_path = Path(project_dir) / workspace_dir
        Path(workspace_path).mkdir(parents=True, exist_ok=True)
        return []
    else:
        return ['<p>A project with this name already exists on the server.</p>']


def project_exists(name, location, WORKSPACE_PROJECTS):
    """Check if the project exists.
    
    Checks the database and the server (if a url to a
    datapackage.json file is supplied).
    """
    if location == 'database':
        result = list(projects_db.find({'name': name}))
        if result:
            return True
        return False
    else:
        dirlist = [item for item in os.listdir(WORKSPACE_PROJECTS) if os.path.isdir(os.path.join(WORKSPACE_PROJECTS, item))]
        if name not in dirlist:
            return True
        return False


def fetch_datapackage(manifest, zip_path, project_dir, workspace_projects, workspace_dir):
    """Fetch a project datapackage from the database."""
    # Get the manifest with content from the database
    manifest = list(projects_db.find({'name': manifest['name']}))
    content = manifest[0].pop('content')
    try:
        # Save the datapackage to disk
        with open(zip_path, 'wb') as f:
            f.write(content)
            print('Wrote the datapackage in fetch_datapackage() to ' + zip_path + '.')
        # Extract the zip archive
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(workspace_projects)
            print('Extracted ' + zip_path + ' in fetch_datapackage() to ' + workspace_projects + '.')
        # Delete the datatapackage
        Path(zip_path).unlink()
        print('Deleted the datapackage in fetch_datapackage() at ' + zip_path + '.')
        # Make a virtual workspace directory in the project.
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)
        print('Made a workspace folder in fetch_datapackage() at ' + workspace_dir + '.')
        return []
    except:
        shutil.rmtree(project_dir)
        return ['<p>Could not extract the project datapackage.</p>']


def validate_corpus_query(query):
    """Make sure the Corpus query returns results."""
    result = list(corpus_db.find(query))
    if result:
        return True
    return False


def make_datapackage(manifest, project_dir, workspace_dir, query):
    """Create a new datapackage from a Corpus query."""
    errors = []
    try:
        datapackage_file = os.path.join(project_dir, 'datapackage.json')
        # Add the resources property and write the subfolders
        # We may need to write files to the virtual workspace
        resources = []
        for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
            resources.append({'path': '/' + folder})
            new_folder = os.path.join(project_dir, folder)
            Path(new_folder).mkdir(parents=True, exist_ok=True)
            print('Made a folder in make_datapackage at ' + new_folder + '.')
        manifest['resources'] = resources + [{'path': '/Workspace'}]
        # Write the datapackage file to the project folder
        with open(datapackage_file, 'w') as f:
            f.write(json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL))
            print('Wrote a datapackage file in make_datapackage at ' + datapackage_file + '.')
    except:
        errors.append('<p>Could not build the project file structure.</p>')
    # Now write the data to the project folder
    try:
        result = list(corpus_db.find(json.loads(query)))
        for doc in result:
            metapath = doc['metapath'].replace(',', '/')
            new_metapath = os.path.join(project_dir, metapath)
            Path(new_metapath).mkdir(parents=True, exist_ok=True)
            print('Made a folder in make_datapackage at ' + new_metapath + '.')
            filepath = os.path.join(new_metapath, doc['name'] + '.json')
            with open(filepath, 'w') as f:
                f.write(json.dumps(doc, indent=2, sort_keys=False, default=JSON_UTIL))
                print('Wrote a manifest file in make_datapackage at ' + filepath + '.')
    except:
        errors.append('<p>Could not write the data to the project directory.</p>')
    return errors


class Datapackage():
    """Models a project datapackage object."""

    def __init__(self, manifest, WORKSPACE_PROJECTS):
        """Initialize the Datapackage object."""
        container_prefix = datetime.now().strftime('%Y%m%d_%H%M_')
        self.workspace_projects = WORKSPACE_PROJECTS
        self.errors = []
        self.manifest = clean(manifest)
        self.query = manifest['db-query']
        self.name = manifest['name']
        self.container = os.path.join(self.workspace_projects, container_prefix + self.name)
        self.project_dir = os.path.join(self.container, self.name)
        self.workspace_dir = os.path.join(self.project_dir, 'Workspace')
        self.zip_name = self.name + '.zip'
        self.zip_path = self.project_dir + '.zip'
        if 'content' in manifest:
            self.content = manifest['content']
        else:
            self.content = ''

        # 1. Make the project folder
        result = make_project_folder(self.project_dir, self.workspace_dir)
        self.errors += result

        # 2. Check whether the project already exists
        if project_exists(self.name, 'database', WORKSPACE_PROJECTS):
            # Get the project from the database
            result = fetch_datapackage(self.manifest, self.zip_path, self.project_dir, self.workspace_projects, self.workspace_dir)
            self.errors += result
            """In case we need to write files to the workspace folder.
            This probably could be moved to fetch_datapackage().
            """
            # if result == []:
            #     populate_workspace(self.projects_dir, self.workspace_dir)
        else:
            # Otherwise, make a datapackage
            if validate_corpus_query(json.loads(self.manifest['db-query'])):
                result = make_datapackage(self.manifest, self.project_dir, self.workspace_dir, self.manifest['db-query'])
                # If there are any errors, delete the container folder
                if result:
                    print('Erasing folder.')
                    # shutil.rmtree(self.container)
                self.errors += result
            else:
                self.errors.append('<p>Could not find any Corpus data. Please test your query.</p>')


class Notebook():
    """Models a Jupyter notebook."""

    def __init__(self, manifest, container, notebook_start, WORKSPACE_PROJECTS, WORKSPACE_TEMPLATES):
        """Write a new Jupyter notebook based on a template in the project directory."""
        # Configurable
        self.errors = []
        self.manifest = manifest
        self.name = manifest['name']
        self.notebook_start = notebook_start
        self.workspace_projects = WORKSPACE_PROJECTS
        self.templates_dir = WORKSPACE_TEMPLATES
        self.container = container
        self.project_dir = os.path.join(self.container, self.name)
        self.workspace_dir = os.path.join(self.project_dir, 'Workspace')
        # Will create /instance/workspace/projects/project_name/Workspace/start.ipynb
        self.output = os.path.join(self.workspace_dir, notebook_start + '.ipynb')
        self.today = datetime.now().strftime('%Y-%m-%d')
        print('output')
        print(self.output)
        # Create a folder for the notebook
        path = re.sub(r'\/start\.ipynb$', '', self.output)
        Path(path).mkdir(parents=True, exist_ok=True)
        # Create a caches directory
        caches_dir = os.path.join(self.workspace_dir, 'caches')
        Path(caches_dir).mkdir(parents=True, exist_ok=True)
        # Create a scripts directory and copy the templates
        scripts_template_dir = os.path.join(self.templates_dir, 'scripts')
        scripts_dir = os.path.join(self.workspace_dir, 'scripts')
        Path(scripts_dir).mkdir(parents=True, exist_ok=True)
        shutil.copytree(scripts_template_dir, scripts_dir, ignore=shutil.ignore_patterns('.ipynb_checkpoints', '__pycache__'))
        dictionary = {}
        try:
            # Retrieve a text file with the notebook cells
            template = os.path.join(self.templates_dir, self.notebook_start + '.txt')
            with open(template, 'r') as f:
                cells = f.read()
            soup = BeautifulSoup(cells, 'lxml')
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
            # Iterate through the template cells
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
            open(self.output, 'w').write(json.dumps(dictionary))
            print('Wrote a notebook in Notebook() at ' + self.output + '.')
            # Copy project values into the settings template
            out = '\n\n## WMS Settings\n'
            out += 'manifest       = ' + json.dumps(self.manifest, indent=2, sort_keys=False, default=JSON_UTIL) + '\n'
            out += "container_dir  = '" + self.container + "'" + "\n"
            out += "project_dir    = '" + self.project_dir + "'" + "\n"
            out += "corpus_dir     = '" + self.project_dir + "/Corpus'" + "\n"
            out += "processes_dir  = '" + self.project_dir + "/Processes'" + "\n"
            out += "scripts_dir    = '" + self.project_dir + "/Scripts'" + "\n"
            out += "sources_dir    = '" + self.project_dir + "/Sources'" + "\n"
            project_settings_path = os.path.join(path, 'settings.py')
            with open(project_settings_path, 'a') as f:
                f.write(out)
        except:
            self.errors.append(['<p>Could not write the initial notebook to the project folder.</p>'])
