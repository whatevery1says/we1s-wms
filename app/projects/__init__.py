"""Projects __init.py__."""

# import: standard
from datetime import datetime
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid
import zipfile
# import: third-party
from bson import BSON, Binary, json_util, ObjectId
import dateutil.parser
from flask import Blueprint, render_template, request, url_for, current_app, send_file
from jsonschema import validate, FormatChecker
import pymongo
from pymongo import MongoClient
import requests
import tabulator
from werkzeug.utils import secure_filename
import yaml
# import: app
from app.projects.helpers import workspace


JSON_UTIL = json_util.default

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
projects_db = db.Projects
corpus_db = db.Corpus

projects = Blueprint('projects', __name__, template_folder='projects')

# ----------------------------------------------------------------------------#
# Constants.
# ----------------------------------------------------------------------------#


ALLOWED_EXTENSIONS = ['zip']
# Horrible hack to get the instance path from out of context
root_path = projects.root_path.replace('\\', '/').split('/')
del root_path[-2:]
instance_path = '/'.join(root_path) + '/instance'
WORKSPACE_DIR = os.path.join(instance_path, 'workspace')
WORKSPACE_TEMP = os.path.join(WORKSPACE_DIR, 'temp')
WORKSPACE_PROJECTS = os.path.join(WORKSPACE_DIR, 'projects')
WORKSPACE_TEMPLATES = os.path.join(WORKSPACE_DIR, 'templates')

# ----------------------------------------------------------------------------#
# Model.
# ----------------------------------------------------------------------------#


class Project():
    """Model a project.

    Parameters:
    - manifest: dict containing form data for the project manifest.
    - query: dict containing the database query.
    - action: the database action to be taken: "insert" or "update".

    Returns a JSON object with the format `{'response': 'success|fail', 'errors': []}`.

    """

    def __init__(self, manifest, query, action):
        """Initialize the object."""
        self.action = action
        self.manifest = self.clean(manifest)
        self.query = json.loads(query)
        self.name = manifest['name']
        self.filename = manifest['name'] + '.zip'

    def clean(self, manifest):
        """Remove empty form values and form builder parameters."""
        data = {}
        for k, v in manifest.items():
            if v not in ['', [], ['']] and not k.startswith('builder_'):
                data[k] = v
        return data

    def exists(self):
        """Test whether the project already exists in the database."""
        test = projects_db.find_one({'name': self.name})
        if test is not None:
            return True
        return False

    def insert(self):
        """Insert a project in the database."""
        unknown_error_msg = 'An unknown error occurred when trying to insert the project into the database.'
        self.manifest['created'] = datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')
        if self.query != {}:
            # Create the datapackage and add it to the manifest with the datetime
            content, errors, key = self.make_datapackage()
            self.manifest['content'] = content
            try:
                # Insert the manifest into the database
                projects_db.insert_one(self.manifest)
                empty_tempfolder(key)
                return {'result': 'success', 'manifest': str(self.manifest['_id']), 'errors': errors}
            except:
                return {'result': 'fail', 'errors': [unknown_error_msg]}
        else:
            self.manifest['content'] = ''
            try:
                # Insert the manifest into the database
                projects_db.insert_one(self.manifest)
                return {'result': 'success', 'manifest': str(self.manifest['_id']), 'errors': []}
            except:
                return {'result': 'fail', 'errors': [unknown_error_msg]}

    def update(self):
        """Update an existing project in the database."""
        saved_project = projects_db.find_one({'name': self.name})
        # The query has not been edited, just update the metadata
        if saved_project['db-query'] == self.manifest['db-query']:
            updated_manifest = {}
            for k, v in self.manifest.items():
                if k not in ['name', '_id', 'content']:
                    updated_manifest[k] = v
            try:
                projects_db.update_one({'_id': ObjectId(saved_project['_id'])},
                                       {'$set': updated_manifest}, upsert=False)
                return {'result': 'success', 'errors': []}
            except pymongo.errors.OperationFailure as e:
                print(e.code)
                print(e.details)
                msg = 'Unknown Error: The record for <code>name</code> <strong>' + \
                    self.name + '</strong> could not be updated.'
                return {'result': 'fail', 'errors': [msg]}
        # The query has been changed, so a new zip archive must be created
        else:
            content, errors, key = self.make_datapackage()
            self.manifest['content'] = content
            _id = self.manifest.pop('_id')
            try:
                projects_db.update_one({'_id': ObjectId(saved_project['_id'])},
                                       {'$set': self.manifest}, upsert=False)
                empty_tempfolder(key)
                return {'result': 'success', 'errors': []}
            except pymongo.errors.OperationFailure as e:
                print(e.code)
                print(e.details)
                msg = 'Unknown Error: The record for <code>name</code> <strong>' + self.name + '</strong> could not be updated.'
                errors.append(msg)
                return {'result': 'fail', 'errors': errors}

    def make_datapackage(self):
        """Create a project folder and zip archive folder containing a data package.

        Returns a binary of the zip archive, a list of errors, and the key to the
        location of the archive in the temp folder.
        """
        errors = []
        # Remove empty form values and form builder parameters
        data = self.manifest

        # Add the resources property -- we're making a datapackage
        resources = []
        for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
            resources.append({'path': '/' + folder})
        data['resources'] = resources

        # Create a unique folder in /workspace/temp and save the datapackage to it
        key = generate_key()
        temp_folder = os.path.join(WORKSPACE_TEMP, key)
        Path(temp_folder).mkdir(parents=True, exist_ok=True)
        # Make a folder with the project name and the standard subfolders
        project_dir = os.path.join(temp_folder, self.name)
        Path(project_dir).mkdir(parents=True, exist_ok=True)
        for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
            new_folder = Path(project_dir) / folder
            Path(new_folder).mkdir(parents=True, exist_ok=True)
        # Write the datapackage file to the project folder
        datapackage = os.path.join(project_dir, 'datapackage.json')
        with open(datapackage, 'w') as f:
            f.write(json.dumps(data, indent=2, sort_keys=False, default=JSON_UTIL))

        # Query the database
        result = list(corpus_db.find(self.query))
        if not result:
            errors.append('No records were found matching your search criteria.')
        else:
            for item in result:
                # Make sure every metapath is a directory
                path = Path(project_dir) / item['metapath'].replace(',', '/')
                Path(path).mkdir(parents=True, exist_ok=True)

                # Write a file for every manifest -- only handles json
                if 'content' in item:
                    filename = item['name'] + '.json'
                    filepath = path / filename
                    with open(filepath, 'w') as f:
                        f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
            # Zip the project_dir to the temp folder and send the file
            self.zipfolder(project_dir, temp_folder, self.name)
            # Read the zip file to a variable and return it
            project_zip = os.path.join(temp_folder, self.filename)
            with open(project_zip, 'rb') as f:
                content = f.read()
            return content, errors, key

    def zipfolder(self, source_dir, temp_folder, output_filename):
        """Create a zip archive of a source directory.

        Takes file paths for both the source directory and the output file.

        Note that the output filename should not have the .zip extension; it is added here.
        """
        output_filepath = os.path.join(temp_folder, output_filename + '.zip')
        zipobj = zipfile.ZipFile(output_filepath, 'w', zipfile.ZIP_DEFLATED)
        rootlen = len(source_dir) + 1
        for base, _, files in os.walk(source_dir):
            for file in files:
                fn = os.path.join(base, file)
                zipobj.write(fn, fn[rootlen:])


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@projects.route('/')
def index():
    """Projects index page."""
    scripts = ['js/corpus/dropzone.js', 'js/projects/projects.js', 'js/projects/upload.js', 'js/jquery-ui.js', 'js/dateformat.js']
    breadcrumbs = [{'link': '/corpus', 'label': 'Scripts'}]
    return render_template('projects/index.html', scripts=scripts, breadcrumbs=breadcrumbs)


@projects.route('/create', methods=['GET', 'POST'])
def create():
    """Create/update project page."""
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/projects/projects.js', 'js/projects/search.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/create', 'label': 'Create/Update Project'}]
    with open('app/templates/projects/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    return render_template('projects/create.html', scripts=scripts, styles=styles, templates=templates, breadcrumbs=breadcrumbs)


# Helpers for /display
def get_default_property(template, prop):
    """Return the first column key in the template for the specified property."""
    for tab in [template['project-template'][0]['required'], template['project-template'][1]['optional']]:
        for item in tab:
            if item['name'] == prop and item['name'] != 'resources':
                return item['cols'][0]


def reshape_list(key, value, template):
    """Reshape a list for the UI.

    Returns either a csv string or the name of the first
    child for the specified property.
    """
    if len(value) > 1 and all(isinstance(item, str) for item in value):
        new_value = ', '.join(value)
    else:
        default = get_default_property(template, key)
        new_value = []
        for item in value:
            if isinstance(item, str):
                new_value.append({default: item})
            else:
                new_value.append(item)
    return new_value


@projects.route('/display/<_id>', methods=['GET', 'POST'])
def display(_id):
    """Display project page."""
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/projects/projects.js', 'js/projects/search.js']
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/projects/display-query.js', 'js/projects/projects.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/create', 'label': 'Display Project'}]
    errors = []
    with open('app/templates/projects/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    manifest = projects_db.find_one({'_id': ObjectId(_id)})
    if manifest is not None:
        # manifest = {'content': ''}
        try:
            if 'db-query' not in manifest:
                manifest['db-query'] = json.dumps({'$and': [{'name': ' '}]})
            if '_id' in manifest:
                manifest['_id'] = str(manifest['_id'])
            manifest['metapath'] = 'Projects'
            # Reshape Lists
            for key, value in manifest.items():
                # The property is a list
                if isinstance(value, list):
                    manifest[key] = reshape_list(key, value, templates)

            # Make sure the manifest has all template properties
            # templates = templates['project-template']
            opts = [templates['project-template'][0]['required'], templates['project-template'][1]['optional']]
            for opt in opts:
                for prop in opt:
                    if prop['name'] not in manifest and prop['fieldtype'] == 'text':
                        manifest[prop['name']] = ''
                    if prop['name'] not in manifest and prop['fieldtype'] == 'textarea':
                        manifest[prop['name']] = ['']
            if 'content' in manifest and manifest['content'] != '':
                manifest['content'] = 'datapackage.json'
            else:
                manifest['content'] = ''
        except:
            errors.append('Unknown Error: Some items in the manifest could not be processed for display.')
    else:
        errors.append('Unknown Error: The project does not exist or could not be loaded.')
    return render_template('projects/display.html', scripts=scripts,
                           breadcrumbs=breadcrumbs, manifest=manifest,
                           errors=errors, templates=templates, styles=styles)


@projects.route('/test-query', methods=['GET', 'POST'])
def test_query():
    """Test whether the project query returns results from the Corpus database."""
    query = request.json
    result = corpus_db.find(query)
    num_results = len(list(result))
    if num_results > 0:
        response = """Your query successfully found records in the Corpus database.
        If you wish to view the results, please use the
        <a href="/corpus/search">Corpus search</a> function."""
    else:
        response = """Your query did not return any records in the Corpus database.
        Try the <a href="/corpus/search">Corpus search</a> function to obtain a
        more accurate query."""
    if not list(corpus_db.find()):
        response = 'The Corpus database is empty.'
    return response


@projects.route('/save-project', methods=['GET', 'POST'])
def save_project():
    """Handle Ajax request data and instantiate the project class.

    Returns a dict containing a result (success or fail) and a list of errors.
    """
    # Get manifest, query, and action from request
    manifest = request.json['manifest']
    query = json.dumps({})
    # if 'db-query' in manifest:
    #     query = manifest.pop(['db-query'])
    action = request.json['action']  # insert or update

    # Instantiate a project object
    project = Project(manifest, query, action)

    # Reject an insert where the project name already exists
    if project.exists() and action == 'insert':
        msg = 'This project name already exists in the database. Please choose another value for <code>name</code>.'
        response = {'result': 'fail', 'errors': [msg]}

    # Update the project
    elif project.exists() and action == 'update':
        response = project.update()
        # empty_tempfolder()

    # Insert a new project
    else:
        response = project.insert()
        # empty_tempfolder()

    # Return a success/fail flag and a list of errors to the browser
    return json.dumps(response)


@projects.route('/delete-datapackage', methods=['GET', 'POST'])
def delete_datapackage():
    """Delete a project datapackage."""
    try:
        projects_db.update_one({'_id': ObjectId(request.json['_id'])},
                    {'$unset': {'content': ''}}, upsert=False)
        response = json.dumps({'result': 'success', 'errors': []})
    except:
        errors = ['<p>Unknown error: The document could not be deleted.</p>']
        response = json.dumps({'result': 'fail', 'errors': errors})
    return response


@projects.route('/delete-project', methods=['GET', 'POST'])
def delete_project():
    """Delete a project."""
    manifest = request.json['manifest']
    result = projects_db.delete_one({'_id': ObjectId(manifest['_id'])})
    if result.deleted_count == 1:
        response = json.dumps({'result': 'success', 'errors': []})
    else:
        errors = ['<p>Unknown error: The document could not be deleted.</p>']
        response = json.dumps({'result': 'fail', 'errors': errors})
    return response


@projects.route('/export-project', methods=['GET', 'POST'])
def export_project():
    """Handle Ajax request data and instantiate the project class.

    Returns a dict containing a result (success or fail) and a list of errors.
    """
    manifest = request.json['manifest']
    query = request.json['query']
    action = request.json['action']  # export
    # Instantiate a project object and make a data pacakge
    project = Project(manifest, query, action)
    _, errors, key = project.make_datapackage()
    if not errors:
        response = {'result': 'success', 'key': key, 'errors': []}
    else:
        response = {'result': 'fail', 'errors': errors}
        empty_tempfolder(key)
    # Return a success/fail flag and a list of errors to the browser
    return json.dumps(response)


@projects.route('/download-export/<filepath>', methods=['GET', 'POST'])
def download_export(filepath):
    """Ajax route to trigger download and empty the temp folder."""
    from flask import make_response
    key, filename = filepath.split('#')
    temp_folder = os.path.join(WORKSPACE_TEMP, key)
    filepath = os.path.join(temp_folder, filename)
    # Can't get Firefox to save the file extension by any means
    with open(filepath, 'rb') as f:
        response = make_response(f.read())
    os.remove(filepath)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
    empty_tempfolder(key)
    return response


@projects.route('/search', methods=['GET', 'POST'])
def search():
    """Experimental Page for searching Projects manifests."""
    scripts = ['js/parsley.min.js', 'js/jquery.twbsPagination.min.js', 'js/query-builder.standalone.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/projects/projects.js', 'js/projects/search.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/search', 'label': 'Search Projects'}]
    if request.method == 'GET':
        return render_template('projects/search.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)
    if request.method == 'POST':
        query = request.json['query']
        page = int(request.json['page'])
        limit = int(request.json['advancedOptions']['limit'])
        sorting = []
        if request.json['advancedOptions']['show_properties'] != []:
            show_properties = request.json['advancedOptions']['show_properties']
        else:
            show_properties = ''
        paginated = True
        sorting = []
        for item in request.json['advancedOptions']['sort']:
            if item[1] == 'ASC':
                opt = (item[0], pymongo.ASCENDING)
            else:
                opt = (item[0], pymongo.DESCENDING)
            sorting.append(opt)
        result, num_pages, errors = search_projects(query, limit, paginated, page, show_properties, sorting)
        if result == []:
            errors.append('No records were found matching your search criteria.')
        # print(result['_id'])
        return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)


@projects.route('/export-search-results', methods=['GET', 'POST'])
def export_search_results():
    """Ajax route for exporting search results."""
    if request.method == 'POST':
        query = request.json['query']
        page = 1
        limit = int(request.json['advancedOptions']['limit'])
        sorting = []
        if request.json['advancedOptions']['show_properties'] != []:
            show_properties = request.json['advancedOptions']['show_properties']
        else:
            show_properties = ''
        paginated = False
        sorting = []
        for item in request.json['advancedOptions']['sort']:
            if item[1] == 'ASC':
                opt = (item[0], pymongo.ASCENDING)
            else:
                opt = (item[0], pymongo.DESCENDING)
            sorting.append(opt)
        result, _, errors = search_projects(query, limit, paginated, page, show_properties, sorting)
        if not result:
            errors.append('No records were found matching your search criteria.')
        else:
            key = generate_key()
            temp_folder = os.path.join(WORKSPACE_TEMP, key)
            # Zip multiple files
            if len(result) > 1:
                zipfolder(temp_folder, 'search-results')
            # Or write a single JSON file
            else:
                filename = os.path.join(temp_folder, 'search-results.json')
                with open(filename, 'w') as f:
                    f.write(json.dumps(result, indent=2, sort_keys=False, default=JSON_UTIL))
        return json.dumps({'filename': filename, 'errors': errors}, default=JSON_UTIL)


@projects.route('/import-project', methods=['GET', 'POST'])
def import_project():
    """Handle import project request."""
    if request.method == 'POST':
        response = {}
        manifest = {}
        errors = []
        file = request.files['file']
        if not file.filename.endswith('.zip'):
            errors.append('The file must be a zip archive ending in <code>.zip</code>.')
        try:
            # Download the zip file and create a manifest
            filename = secure_filename(file.filename)
            key = generate_key()
            temp_folder = os.path.join(WORKSPACE_TEMP, key)
            file_to_save = os.path.join(temp_folder, filename)
            # file_to_save = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            # file_to_save = os.path.join('app', file_to_save)
            file.save(file_to_save)
        except:
            errors.append('Could not save file to disk')
        # Build the manifest from the datapackage
        manifest = manifest_from_datapackage(file_to_save)
        if 'error' in manifest:
            errors.append(manifest['error'])
        # Empty the temporary folder
        # UPLOAD_DIR = Path(os.path.join('app', current_app.config['UPLOAD_FOLDER']))
        # shutil.rmtree(UPLOAD_DIR)
        # UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(temp_folder)

        # Attempt to insert the manifest in the database
        try:
            test = {'name': manifest['name'], 'metapath': 'Projects'}
            result = projects_db.find(test)
            assert list(result)
            projects_db.insert_one(manifest)
        except:
            errors.append('The database already contains a project with the same name.')
        # Create a response to send to the browser
        if errors == []:
            del manifest['content']
            response = {'result': 'success', 'manifest': manifest, 'errors': errors}
        else:
            response = {'result': 'fail', 'manifest': manifest, 'errors': errors}
        return json.dumps(response, indent=2, sort_keys=False, default=JSON_UTIL)


@projects.route('/launch-notebook', methods=['GET', 'POST'])
def launch_notebook():
    """Create a project folder on the server.

    Really simple test to create a project folder and save a file to it.
    The project is saved to (e.g.)
    we1s-wms/instance/workspace/topic-modeling/
    followed by the manifest name + _id
    """
    errors = []
    workflow = request.json['workflow']
    manifest = request.json['manifest']
    if '_id' in manifest:
        project_dirname = manifest['name'] + '_' + manifest['_id']
    else:
        project_dirname = manifest['name'] + '_' + '1234'
    workspace_path = os.path.join(current_app.instance_path, 'workspace')
    workflow_path = os.path.join(workspace_path, workflow)
    project_path = os.path.join(workflow_path, project_dirname)
    print(project_path)
    try:
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        filename = os.path.join(project_path, 'test.txt')
        with open(filename, 'w') as f:
            f.write('test')
    except:
        errors.append('Could not make project directory.')
    return json.dumps({'errors': errors})


@projects.route('/launch-jupyter', methods=['GET', 'POST'])
def launch_jupyter():
    """Create a project folder on the server.

    Produces a project datapackage, along with any workspace templates.
    If successful, the Jupyter notebook is lost; otherwise, an error report
    is returned to the front end.
    """
    errors = []
    manifest = request.json['manifest']
    # The folder containing the notebook (e.g. we1s-topic-modeling)
    notebook_type = 'we1s-' + request.json['notebook']
    # Notebook to launch
    notebook_start = notebook_type + '/start'
    # Path to notebook
    # path = manifest['name'] + '/Workspace/' + notebook_start + '.ipynb'
    # Fetch or create a datapackage based on the info received
    datapackage = workspace.Datapackage(manifest, WORKSPACE_PROJECTS)
    errors += datapackage.errors
    # If the datapackage has no errors, create the notebook
    if not errors:
        notebook = workspace.Notebook(datapackage.manifest, datapackage.container, notebook_start, WORKSPACE_PROJECTS, WORKSPACE_TEMPLATES)
        errors += notebook.errors
    # If the notebook has no errors, launch it
        try:
            print('Launching from ' + notebook.output + '.')
            subprocess.run(['nbopen', notebook.output], stdout=subprocess.PIPE)
        except:
            errors.append('<p>Could not launch the Jupyter notebook.</p>')
    # If the process has accumulated errors on the way, send the
    # error messages to the front end.
    if errors:
        response = json.dumps({'result': 'fail', 'errors': errors})
    else:
        response = json.dumps({'result': 'success', 'errors': []})
    return response


# ----------------------------------------------------------------------------#
# Helpers.
# ----------------------------------------------------------------------------#


def generate_key():
    """Generate a UUID to use as a workspace folder key."""
    uid = uuid.uuid4()
    dirlist = [item for item in os.listdir(WORKSPACE_TEMP) if os.path.isdir(os.path.join(WORKSPACE_TEMP, item))]
    if uid.hex in dirlist:
        generate_key()
    else:
        return uid.hex


def empty_tempfolder(key):
    """Empty the termporary folder specified by the key."""
    # temp_folder = Path(os.path.join('app', current_app.config['TEMP_FOLDER']))
    temp_folder = Path(os.path.join(WORKSPACE_TEMP, key))
    shutil.rmtree(temp_folder)
    temp_folder.mkdir(parents=True, exist_ok=True)


def search_projects(query, limit, paginated, page, show_properties, sorting):
    """Use the query generated in /search and returns the search results."""
    page_size = 10
    errors = []
    if list(projects_db.find()):
        result = projects_db.find(
            query,
            limit=limit,
            projection=show_properties)
        if sorting != []:
            result = result.sort(sorting)
        result = list(result)
        if result != []:
            # Double the result for testing
            # result = result + result + result + result + result
            # result = result + result + result + result + result
            if paginated is True:
                pages = list(paginate(result, page_size=page_size))
                num_pages = len(pages)
                page = get_page(pages, page)
                response = page, num_pages, errors
            else:
                response = result, 1, errors
        else:
            response = [], 1, errors
    else:
        errors.append('The Projects database is empty.')
        response = [], 1, errors
    return response


def get_page(pages, page):
    """Take a list of paginated results form `paginate()` and returns a single page from the list."""
    try:
        return pages[page - 1]
    except:
        print('The requested page does not exist.')


def paginate(iterable, page_size):
    """Return a generator with a list sliced into pages by the designated size.

    If the generator is converted to a list called `pages`, and individual page
    can be called with `pages[0]`, `pages[1]`, etc.
    """
    while True:
        i1, i2 = itertools.tee(iterable)
        iterable, page = (itertools.islice(i1, page_size, None),
                          list(itertools.islice(i2, page_size)))
        if not page:
            break
        yield page


def zipfolder(source_dir, output_filename):
    """Create a zip archive of a source directory.

    Duplicates method in Project class.

    Note that the output filename should not have the
    .zip extension; it is added here.
    """
    temp_folder = os.path.join('app', current_app.config['TEMP_FOLDER'])
    output_filepath = os.path.join(temp_folder, output_filename + '.zip')
    zipobj = zipfile.ZipFile(output_filepath, 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(source_dir) + 1
    for base, _, files in os.walk(source_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


def manifest_from_datapackage(zipfilepath):
    """Generate a project manifest from a zipped datapackage.

    The zip file is embedded in the `content` property, so the project manifest
    is read for insertion in the database.
    """
    # Get the datapackage.json file
    manifest = {}
    try:
        with zipfile.ZipFile(zipfilepath) as z:
            # Get a list of folders beginning with 'Corpus'
            metapath = list(set([os.path.split(x)[0] for x in z.namelist() if '/' in x and x.startswith('Corpus')]))
            with z.open('datapackage.json') as f:
                # Read the datapackage file
                datapackage = json.loads(f.read())
        # Build a manifest from the datapackage info
        manifest['name'] = datapackage['name']
        manifest['metapath'] = 'Projects'
        manifest['namespace'] = 'we1sv2.0'
        manifest['title'] = datapackage['title']
        manifest['contributors'] = datapackage['contributors']
        manifest['created'] = datapackage['created']
        # If the datapackage has a db-query, copy it
        if 'db-query' in datapackage.keys():
            manifest['db-query'] = datapackage['db-query']
        # Otherwise, get the collection path from the zip archive
        else:
            metapath = metapath[0].split('/')
            collection_path = metapath[0] + ',' + metapath[1]
            manifest['db-query'] = '{"$and":[{"metapath":{"$regex":"^' + collection_path + '"}}]}'
        # Now handle the binary attachment
        with open(zipfilepath, 'rb') as f:
            content = f.read()
        manifest['content'] = content
    except:
        manifest['error'] = 'The zip archive does not possess a <code>datapackage.json</code> file, or the file could not be parsed.'
    # Return the manifest
    return manifest


def textarea2dict(fieldname, textarea, main_key, valid_props):
    """Convert a textarea string to a dict with a list of properties for each line.

    Multiple properties should be formatted as comma-separated key: value pairs.
    The key must be separated from the value by a space, and the main key should
    come first. If ": " occurs in the value, the entire value can be put in quotes.
    Where there is only one value, the key can be omitted, and it will be supplied
    from main_key. A list of valid properties is supplied in valid_props. If any
    property is invalid the function returns a dict with only the error key and a
    list of errors.
    """
    lines = textarea.split('\n')
    all_lines = []
    errors = []

    for line in lines:
        # No options
        if main_key == '':
            all_lines.append(line.strip())
        # Parse options
        else:
            opts = {}
            # Match main_key without our without quotation marks
            main = main_key + '|[\'\"]' + main_key + '[\'\"]'
            pattern = ', (' + '[a-z]+: ' + ')'  # Assumes no camel case in the property name
            # There are options. Parse them.
            if re.search(pattern, line):
                line = re.sub(pattern, '\n\\1', line)  # Could be improved to handle more variations
                opts = yaml.load(line.strip())
                for k, _v in opts.items():
                    if valid_props != [] and k not in valid_props:
                        errors.append('The ' + fieldname + ' field is incorrectly formatted or ' + k + ' is not a valid property for the field.')
            # There are no options, but the main_key is present
            elif re.search('^' + main + ': .+$', line):
                opts[main_key] = re.sub('^' + main + ': ', '', line.strip())
            # There are no options, and the main_key is omitted
            elif re.search(pattern, line) is None:
                opts[main_key] = line.strip()
            all_lines.append(opts)
    if errors == []:
        d = {fieldname: all_lines}
    else:
        d = {'errors': errors}
    return d


def dict2textarea(props):
    """Convert a dict to a line-delimited string to return to the UI as the value of a textarea."""
    lines = ''
    for item in props:
        line = ''
        # Handle string values
        if isinstance(item, str):
            lines += item + '\n'
        # Handle dicts
        else:
            for k, v in item.items():
                line += k + ': ' + str(v).strip(': ') + ', '
            lines += line.strip(', ') + '\n'
    return lines.strip('\n')


def testformat(s):
    """Parse a date and return a dict.

    The dict contains the date string, format, and an error message
    if the date cannot be parsed.
    """
    error = ''
    try:
        d = datetime.strptime(s, '%Y-%m-%d')
        dateformat = 'date'
    except:
        try:
            d = datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
            dateformat = 'datetime'
        except:
            dateformat = 'unknown'
    if dateformat == 'unknown':
        try:
            d = dateutil.parser.parse(s)
            # s = d.strftime("%Y-%m-%dT%H:%M:%SZ")
            # dateformat = 'datetime'
            s = d.strftime("%Y-%m-%d")
            dateformat = 'date'
        except:
            error = 'Could not parse date "' + s + '" into a valid format.'
    if error == '':
        response = {'text': s, 'format': dateformat}
    else:
        response = {'text': s, 'format': 'unknown', 'error': error}
    return response


def textarea2datelist(textarea):
    """Convert a textarea string into a list of date dicts."""
    lines = textarea.replace('-\n', '- \n').split('\n')
    all_lines = []
    for line in lines:
        line = line.replace(', ', ',')
        dates = line.split(',')
        for item in dates:
            if re.search(' - ', item):  # Check for ' -'
                d = {'range': {'start': ''}}
                date_range = item.split(' - ')
                start = testformat(date_range[0])
                end = testformat(date_range[1])
                # Make sure start date precedes end date
                try:
                    if end['text'] == '':
                        d['range']['start'] = start
                    else:
                        assert start['text'] < end['text']
                        d['range']['start'] = start
                        d['range']['end'] = end
                except:
                    d = {'error': 'The start date "' + start['text'] + '" must precede the end date "' + end['text'] + '".'}
                else:
                    d['range']['start'] = start
            else:
                d = testformat(item)
            all_lines.append(d)
    return all_lines


def flatten_datelist(all_lines):
    """Flatten the output of textarea2datelist().

    Removes 'text' and 'format' properties and replaces their container dicts
    with a simple date string.
    """
    flattened = []
    for line in all_lines:
        if 'text' in line:
            line = line['text']
        if 'range' in line:
            line['range']['start'] = line['range']['start']['text']
            if 'end' in line['range'] and line['range']['end'] == '':
                line['range']['end'] = line['range']['end']['text']
            elif 'end' in line['range'] and line['range']['end'] != '':
                line['range']['end'] = line['range']['end']['text']
        flattened.append(line)
    return flattened


def serialize_datelist(flattened_datelist):
    """Convert the output of flatten_datelist() to a line-delimited string.

    The string is suitable for returning to the UI as the value of a textarea.
    """
    dates = []
    for item in flattened_datelist:
        if isinstance(item, dict) and 'error' not in item:
            start = item['range']['start'] + ' - '
            if 'end' in item['range']:
                end = item['range']['end']
                dates.append(start + end)
            else:
                dates.append(start)
        else:
            dates.append(str(item))  # error dict is cast as a string
    return '\n'.join(dates)
