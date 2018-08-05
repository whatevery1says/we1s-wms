import itertools
import json
import os
import re
import requests
import shutil
import zipfile

import tabulator
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from jsonschema import validate, FormatChecker

# For various solutions to dealing with ObjectID, see
# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
# If speed becomes an issue: https://github.com/mongodb-labs/python-bsonjs
from bson import BSON, Binary, json_util
JSON_UTIL = json_util.default

from jsonschema import validate, FormatChecker
from flask import Blueprint, render_template, request, url_for, current_app, send_file
from werkzeug.utils import secure_filename

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
scripts_db = db.Scripts

scripts = Blueprint('scripts', __name__, template_folder='scripts')

# from app.scripts.helpers import methods as methods
# from app.scripts.helpers import workspace as workspace

# ----------------------------------------------------------------------------#
# Constants.
# ----------------------------------------------------------------------------#


ALLOWED_EXTENSIONS = ['zip']

# ----------------------------------------------------------------------------#
# Model.
# ----------------------------------------------------------------------------#


class Script():
    """Models a script or tool. Parameters:
    manifest: dict containing form data for the script or tool manifest
    query: dict containing the database query
    action: the database action to be taken: "insert" or "update"
    Returns a JSON object: `{'response': 'success|fail', 'errors': []}`"""

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
            if v != '' and not k.startswith('builder_'):
                data[k] = v
        return data

    def exists(self):
        """Test whether the script or tool already exists in the database."""
        test = scripts_db.find({'metapath': 'Scripts', 'name': self.name})
        if len(list(test)) > 0:
            return True
        else:
            return False

    def insert(self):
        """Insert a script or tool in the database."""
        try:
            # Create the datapackage and add it to the manifest
            content, errors = self.make_datapackage()
            self.manifest['content'] = content
            # Insert the manifest into the database
            scripts_db.insert_one(self.manifest)
            return {'result': 'success', 'errors': errors}
        except:
            msg = """An unknown error occurred when trying to
            insert the script or tool into the database."""
            return {'result': 'fail', 'errors': [msg]}

    def update(self):
        """Update an existing script or tool in the database."""
        saved_script = scripts_db.find({'metapath': 'Scripts', 'name': self.name})
        # The query has not been edited, just update the metadata
        if saved_script[0]['db-query'] == self.manifest['db-query']:
            updated_manifest = {}
            for k, v in self.manifest.items():
                if k not in ['name', '_id', 'content']:
                    updated_manifest[k] = v
            try:
                scripts_db.update_one({'name': self.name}, {
                                '$set': updated_manifest}, upsert=False)
                return {'result': 'success', 'errors': []}
            except pymongo.errors.PyMongoError as e:
                print(e.__dict__.keys())
                # print(e._OperationFailure__details)
                msg = 'Unknown Error: The record for <code>name</code> <strong>' + \
                    self.name + '</strong> could not be updated.'
                return {'result': 'fail', 'errors': [msg]}
        # The query has been changed, so a new zip archive must be created
        else:
            content, errors = self.make_datapackage()
            self.manifest['content'] = content
            try:
                scripts_db.update_one({'name': self.name}, {'$set': self.manifest}, upsert=False)
                return {'result': 'success', 'errors': []}
            except pymongo.errors.PyMongoError as e:
                print(e.__dict__.keys())
                # print(e._OperationFailure__details)
                msg = 'Unknown Error: The record for <code>name</code> <strong>' + self.name + '</strong> could not be updated.'
                errors.append(msg)
                return {'result': 'fail', 'errors': errors}


    def make_datapackage(self):
        """Create a script or tool folder containing a data pacakage, then
        make a zip archive of the folder. Returns a binary of the
        zip archive and a list of errors."""
        errors = []
        # Remove empty form values and form builder parameters
        data = {}
        for k, v in self.manifest.items():
            if v != '' and not k.startswith('builder_'):
                data[k] = v

        # Add the resources property -- we're making a datapackage
        resources = []
        for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
            resources.append({'path': '/' + folder})
        data['resources'] = resources

        # Create the script or tool folder and save the datapackage to it
        temp_folder = os.path.join('app', current_app.config['TEMP_FOLDER'])
        script_dir = os.path.join(temp_folder, self.name)
        Path(script_dir).mkdir(parents=True, exist_ok=True)
        # Make the standard subfolders
        for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
            new_folder = Path(script_dir) / folder
            Path(new_folder).mkdir(parents=True, exist_ok=True)
        # Write the datapackage file to the script or tool folder
        datapackage = os.path.join(script_dir, 'datapackage.json')
        with open(datapackage, 'w') as f:
            f.write(json.dumps(data, indent=2, sort_keys=False, default=JSON_UTIL))

        # Query the database
        result = list(corpus_db.find(self.query))
        if len(result) == 0:
            errors.append('No records were found matching your search criteria.')
        else:
            for item in result:
                # Make sure every metapath is a directory
                path = Path(script_dir) / item['metapath'].replace(',', '/')
                Path(path).mkdir(parents=True, exist_ok=True)

                # Write a file for every manifest -- only handles json
                if 'content' in item:
                    filename = item['name'] + '.json'
                    filepath = path / filename
                    with open(filepath, 'w') as f:
                        f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
            # Zip the script_dir to the temp folder and send the file
            self.zipfolder(script_dir, self.name)
            # Read the zip file to a variable and return it
            script_zip = os.path.join(temp_folder, self.filename)
            with open(script_zip, 'rb') as f:
                content = f.read()
            return content, errors


    def zipfolder(self, source_dir, output_filename):
        """Creates a zip archive of a source directory.

        Takes file paths for both the source directory
        and the output file.

        Note that the output filename should not have the
        .zip extension; it is added here.
        """
        temp_folder = os.path.join('app', current_app.config['TEMP_FOLDER'])
        output_filepath = os.path.join(temp_folder, output_filename + '.zip')
        zipobj = zipfile.ZipFile(output_filepath, 'w', zipfile.ZIP_DEFLATED)
        rootlen = len(source_dir) + 1
        for base, dirs, files in os.walk(source_dir):
            for file in files:
                fn = os.path.join(base, file)
                zipobj.write(fn, fn[rootlen:])


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@scripts.route('/')
def index():
    """Scripts index page."""
    scripts = ['js/corpus/dropzone.js', 'js/scripts/scripts.js', 'js/scripts/upload.js', 'js/dateformat.js', 'js/jquery-ui.js']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}]
    return render_template('scripts/index.html', scripts=scripts, breadcrumbs=breadcrumbs)


@scripts.route('/create', methods=['GET', 'POST'])
def create():
    """Create/update script or tool page."""
    scripts = ['js/corpus/dropzone.js', 'js/parsley.min.js', 'js/moment.min.js', 'js/scripts/scripts.js', 'js/scripts/upload.js', 'js/dateformat.js', 'js/jquery-ui.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}, {'link': '/scripts/create', 'label': 'Create/Update Script'}]
    with open('app/templates/scripts/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    return render_template('scripts/create.html', scripts=scripts, styles=styles, templates=templates, breadcrumbs=breadcrumbs)


@scripts.route('/display/<name>', methods=['GET', 'POST'])
def display(name):
    """Display script or tool page."""
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery-sortable-min.js', 'js/scripts/scripts.js', 'js/scripts/search.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}, {'link': '/scripts/create', 'label': 'Display Script'}]
    errors = []
    manifest = {}
    with open('app/templates/scripts/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    try:
        result = scripts_db.find({'name': name})
        assert result != None
        manifest = list(result)[0]
        del manifest['content']
        for key, value in manifest.items():
            if isinstance(value, list):
                textarea = str(value)
                textarea = dict2textarea(value)
                manifest[key] = textarea
            else:
                manifest[key] = str(value)
        manifest['metapath'] = 'Scripts'
    except:
        errors.append('Unknown Error: The script or tool does not exist or could not be loaded.')
    return render_template('scripts/display.html', scripts=scripts,
        breadcrumbs=breadcrumbs, manifest=manifest, errors=errors,
        templates=templates, styles=styles)


@scripts.route('/test-query', methods=['GET', 'POST'])
def test_query():
    """Tests whether the script or tool query returns results
    from the Corpus database."""
    query = json.loads(request.json['db-query'])
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
    if len(list(corpus_db.find())) == 0:
        response = 'The Corpus database is empty.'
    return response


@scripts.route('/save-script', methods=['GET', 'POST'])
def save_script():
    """ Handles Ajax request data and instantiates the script or tool class.
    Returns a dict containing a result (success or fail) and a list
    of errors."""
    query = request.json['query']
    action = request.json['action']  # insert or update
    data = request.json['manifest']
    manifest = {}
    # Get rid of empty values
    for key, value in data.items():
        if value != '':
            manifest[key] = value
    # Convert dates strings to lists
    if 'created' in manifest.keys():
        created = flatten_datelist(textarea2datelist(manifest['created']))
        if isinstance(created, list) and len(created) == 1:
            created = created[0]
        manifest['created'] = created
    if 'updated' in manifest.keys():
        updated = flatten_datelist(textarea2datelist(manifest['updated']))
        if isinstance(updated, list) and len(updated) == 1:
            updated = updated[0]
        manifest['updated'] = updated
    # Handle other textarea strings
    list_props = ['contributors', 'created', 'notes', 'keywords', 'licenses', 'updated']
    prop_keys = {
        'contributors': { 'main_key': 'title', 'valid_props': ['title', 'email', 'path', 'role', 'group', 'organization'] },
        'licenses': { 'main_key': 'name', 'valid_props': ['name', 'path', 'title'] },
        'created': { 'main_key': '', 'valid_props': [] },
        'updated': { 'main_key': '', 'valid_props': [] },
        'notes': { 'main_key': '', 'valid_props': [] },
        'keywords': { 'main_key': '', 'valid_props': [] }
    }
    for item in list_props:
        if item in manifest and manifest[item] != '':
            all_lines = textarea2dict(item, manifest[item], prop_keys[item]['main_key'], prop_keys[item]['valid_props'])
            if all_lines[item] != []:
                manifest[item] = all_lines[item]
    # Instantiate a script or tool object
    script = Script(manifest, query, action)
    # Reject an insert where the script or tool name already exists
    if script.exists() and action == 'insert':
        print('Duplicate script or tool cannot be inserted.')
        msg = 'This script or tool name already exists in the database. Please choose another value for <code>name</code>.'
        response = {'result': 'fail', 'errors': [msg]}
    # Update the script or tool
    elif script.exists() and action == 'update':
        response = script.update()
        empty_tempfolder()
    # Insert a new script or tool
    else:
        response = script.insert()
        empty_tempfolder()
    # Return a success/fail flag and a list of errors to the browser
    return json.dumps(response)


@scripts.route('/delete-script', methods=['GET', 'POST'])
def delete_script():
    manifest = request.json['manifest']
    print('Deleting...')
    result = scripts_db.delete_one({'name': manifest['name'], 'metapath': 'Scripts'})
    if result.deleted_count != 0:
        print('success')
        return json.dumps({'result': 'success', 'errors': []})
    else:
        print('Unknown error: The document could not be deleted.')
        return json.dumps({'result': 'fail', 'errors': result})


@scripts.route('/export-script', methods=['GET', 'POST'])
def export_script():
    """ Handles Ajax request data and instantiates the script class.
    Returns a dict containing a result (success or fail) and a list
    of errors."""
    print(request.json)
    manifest = request.json['manifest']
    query = request.json['query']
    action = request.json['action']  # export
    # Instantiate a script object and make a data pacakge
    script = Script(manifest, query, action)
    content, errors = script.make_datapackage()
    if len(errors) == 0:
        response = {'result': 'success', 'errors': []}
    else:
        response = {'result': 'fail', 'errors': errors}
        empty_tempfolder()
    # Return a success/fail flag and a list of errors to the browser
    return json.dumps(response)


@scripts.route('/download-export/<filename>', methods=['GET', 'POST'])
def download_export(filename):
    """ Ajax route to trigger download and empty the temp folder."""
    from flask import make_response
    filepath = os.path.join('app/temp', filename)
    # Can't get Firefox to save the file extension by any means
    with open(filepath, 'rb') as f:
        response = make_response(f.read())
    os.remove(filepath)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
    empty_tempfolder()
    return response


@scripts.route('/search', methods=['GET', 'POST'])
def search():
    """ Experimental Page for searching Scripts manifests."""
    scripts = ['js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/scripts/scripts.js', 'js/jquery-sortable-min.js', 'js/scripts/search.js', 'js/dateformat.js', 'js/jquery-ui.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}, {'link': '/scripts/search', 'label': 'Search Scripts'}]
    if request.method == 'GET':
        return render_template('scripts/search.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)
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
        result, num_pages, errors = search_scripts(query, limit, paginated, page, show_properties, sorting)
        if result == []:
            errors.append('No records were found matching your search criteria.')
        return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)


@scripts.route('/export-search-results', methods=['GET', 'POST'])
def export_search_results():
    """ Ajax route for exporting search results."""
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
        result, num_pages, errors = search_scripts(query, limit, paginated, page, show_properties, sorting)
        if len(result) == 0:
            errors.append('No records were found matching your search criteria.')
        # Need to write the results to temp folder
        for item in result:
            filename = 'search-results.zip'
            filepath = 'app/temp/search-results.zip'
            with open(filepath, 'w') as f:
                f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
        # Need to zip up multiple files
        if len(result) > 1:
            filename = 'search-results.zip'
            zipfolder('app/temp', 'search-results')
        return json.dumps({'filename': filename, 'errors': errors}, default=JSON_UTIL)


@scripts.route('/import-script', methods=['GET', 'POST'])
def import_script():
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
            file_to_save = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file_to_save = os.path.join('app', file_to_save)
            file.save(file_to_save)
        except:
            errors.append('Could not save file to disk')
        # Build the manifest from the datapackage
        manifest = manifest_from_datapackage(file_to_save)
        if 'error' in manifest:
            errors.append(manifest['error'])
        # Empty the uploads folder
        UPLOAD_DIR = Path(os.path.join('app', current_app.config['UPLOAD_FOLDER']))
        shutil.rmtree(UPLOAD_DIR)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        # Attempt to insert the manifest in the database
        try:
            test = {'name': manifest['name'], 'metapath': 'Scripts'}
            result = scripts_db.find(test)
            assert len(list(result)) > 0
            scripts_db.insert_one(manifest)
        except:
            errors.append('The database already contains a script or tool with the same name.')
        # Create a response to send to the browser
        if errors == []:
            del manifest['content']
            response = {'result': 'success', 'manifest': manifest, 'errors': errors}
        else:
            response = {'result': 'fail', 'manifest': manifest, 'errors': errors}
        return json.dumps(response, indent=2, sort_keys=False, default=JSON_UTIL)


def load_saved_datapackage(manifest, zip_filepath, scripts_dir, workspace_dir):
    content = manifest.pop('content')
    # Save the datapackage to disk
    with open(zip_filepath, 'rb') as f:
        f.write(content)
    # Extract the zip archive
    with zipfile.ZipFile(zip_filepath) as zf:
        zf.extractall(scripts_dir)
    # Delete the datatapackage
        os.remove(zip_filepath)
    # Make a virtual workspace directory in the script or tool.
    # We may need to write workspace files to it.
    Path(workspace_dir).mkdir(parents=True, exist_ok=True)


def make_new_datapackage(script_dir, data):
    # Make sure the Corpus query returns results
    errors = []
    try:
        result = list(corpus_db.find(data['db_query']))
        assert len(result) > 0
    except:
        errors.append('<p>Could not find any Corpus data. Please test your query.</p>')
    if len(result) > 0:
        try:
            # Remove empty form values and form builder parameters
            manifest = {}
            for k, v in data.items():
                if v != '' and not k.startswith('builder_'):
                    manifest[k] = v
            # Add the resources property -- we're making a datapackage
            resources = []
            for folder in ['Sources', 'Corpus', 'Processes', 'Scripts']:
                resources.append({'path': '/' + folder})
            manifest['resources'] = resources
            # Add the standard subfolders to the script or tool folder
            # We may need to write files to the virtual workspace
            for folder in ['Sources', 'Corpus', 'Processes', 'Scripts', 'Virtual_Workspace']:
                new_folder = Path(script_dir) / folder
                Path(new_folder).mkdir(parents=True, exist_ok=True)
            # Write the datapackage file to the script or tool folder
            datapackage = os.path.join(script_dir, 'datapackage.json')
            with open(datapackage, 'r') as f:
                f.write(json.dumps(manifest))
        except:
            errors.append('<p>Could not write the datapackage to the script or tool directory.</p>')
        # Now write the data to the script or tool folder
        try:
            for doc in result:
                metapath = doc['metapath'].replace(',', '/')
                path = os.path.join(metapath, doc['name'] + '.json')
                filepath = os.path.join(script_dir, path)
                with open(filepath, 'w') as f:
                    f.write(doc)
        except:
            errors.append('<p>Could not write the data to the script directory.</p>')
    return errors


@scripts.route('/launch-jupyter', methods=['GET', 'POST'])
def launch_jupyter():
    """ Creates a script folder on the server containing a
    script datapackage, along with any workspace templates.
    If successful, the Jupyter notebook is lost; otherwise,
    an error report is returned to the front end."""
    errors = []
    manifest = request.json['manifest']
    scripts_dir = 'https://mirrormask.english.ucsb.edu:9999/scripts'
    file_path = 'path_to_starting_notebook'
    # Fetch or create a datapackage based on the info received
    datapackage = workspace.Datapackage(manifest, scripts_dir)
    errors += datapackage.errors
    # If the datapackage has no errors, create the notebook
    if len(errors) == 0:
        notebook = workspace.Notebook(datapackage.manifest, scripts_dir)
        errors += notebook.errors
    # If the notebook has no errors, launch it
        try:
            subprocess.run(['nbopen', file_path], stdout=subprocess.PIPE)
        except:
            errors.append('<p>Could not launch the Jupyter notebook.</p>')
    # If the process has accumulated errors on the way, send the
    # error messages to the front end.
    if len(errors) > 0:
        return json.dumps({'result': 'fail', 'errors': errors})
    else:
        return json.dumps({'result': 'success', 'errors': []})


# Old Method -- not used
@scripts.route('/launch-jupyter-old', methods=['GET', 'POST'])
def launch_jupyter_old():
    """ Experimental Page to launch a Jupyter notebook."""
    errors = []
    scripts_dir = "https://mirrormask.english.ucsb.edu:9999/scripts"
    script_name = request.json['data']['name']
    script_dir = os.path.join(scripts_dir, script_name)
    workspace_dir = os.path.join(script_dir, 'Virtual_Workspace')
    zip_filepath = script_dir + '.zip'
    # Make script folder if it does not exist
    if not Path(script_dir).exists():
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)
    else:
        errors.append('<p>A script or tool with this name already exists on the server.</p>')
    # Check if the script or tool is in the database
    result = list(scripts_db.find({'name': script_name}))
    # If the script is saved to the database
    if len(result) > 0:
        try:
            load_saved_datapackage(result, zip_filepath, scripts_dir, workspace_dir)
        except:
            errors.append('<p>There was an error saving the script datapackage to the server.</p>')
    # Otherwise, make a new datapackage
    else:
        try:
            errors = make_new_datapackage(script_dir, request.json['data'])
        except:
            errors.append('<p>There was an error creating the script datapackage on the server.</p>')
    return errors

# Now we need to write the notebook file and then launch it.
#         # Launch the notebook
#         filename = manifest['name'] + '.ipynb'
#         file_path = os.path.join('app', filename)
#         with open(file_path, 'w') as f:
#             f.write(doc)
#         subprocess.run(['nbopen', file_path], stdout=subprocess.PIPE)
#         return 'success'
#     except:
#         return 'error'

# ----------------------------------------------------------------------------#
# Helpers.
# ----------------------------------------------------------------------------#


def empty_tempfolder():
    temp_folder = Path(os.path.join('app', current_app.config['TEMP_FOLDER']))
    shutil.rmtree(temp_folder)
    temp_folder.mkdir(parents=True, exist_ok=True)


def search_scripts(query, limit, paginated, page, show_properties, sorting):
    """Uses the query generated in /search and returns the search results.
    """
    page_size = 10
    errors = []
    if len(list(scripts_db.find())) > 0:
        result = scripts_db.find(
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
                return page, num_pages, errors
            else:
                return result, 1, errors
        else:
            return [], 1, errors
    else:
        errors.append('The Scripts database is empty.')
        return [], 1, errors


def get_page(pages, page):
    """Takes a list of paginated results form `paginate()` and
    returns a single page from the list.
    """
    try:
        return pages[page-1]
    except:
        print('The requested page does not exist.')


def paginate(iterable, page_size):
    """Returns a generator with a list sliced into pages by the designated size. If
    the generator is converted to a list called `pages`, and individual page can
    be called with `pages[0]`, `pages[1]`, etc.
    """
    while True:
        i1, i2 = itertools.tee(iterable)
        iterable, page = (itertools.islice(i1, page_size, None),
            list(itertools.islice(i2, page_size)))
        if len(page) == 0:
            break
        yield page


def zipfolder(source_dir, output_filename):
    """Creates a zip archive of a source directory.

    Duplicates method in Script class.

    Note that the output filename should not have the
    .zip extension; it is added here.
    """
    temp_folder = os.path.join('app', current_app.config['TEMP_FOLDER'])
    output_filepath = os.path.join(temp_folder, output_filename + '.zip')
    zipobj = zipfile.ZipFile(output_filepath, 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(source_dir) + 1
    for base, dirs, files in os.walk(source_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


def manifest_from_datapackage(zipfilepath):
    """Generates a script manifest from a zipped datapackage. The zip file is
    embedded in the `content` property, so the script manifest is read for
    insertion in the database."""
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
        manifest ['name'] = datapackage['name']
        manifest ['metapath'] = 'Scripts'
        manifest['namespace'] = 'we1sv2.0'
        manifest ['title'] = datapackage['title']
        manifest ['contributors'] = datapackage['contributors']
        manifest ['created'] = datapackage['created']
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
    """Converts a textarea string to a dict containing a list of
    properties for each line. Multiple properties should be
    formatted as comma-separated key: value pairs. The key must be
    separated from the value by a space, and the main key should come
    first. If ": " occurs in the value, the entire value can be put in
    quotes. Where there is only one value, the key can be omitted, and
    it will be supplied from main_key. A list of valid properties is
    supplied in valid_props. If any property is invalid the function
    returns a dict with only the error key and a list of errors.
    """
    import yaml
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
            pattern = ', (' +'[a-z]+: ' + ')' # Assumes no camel case in the property name
            # There are options. Parse them.
            if re.search(pattern, line):
                line = re.sub(pattern, '\n\\1', line)  # Could be improved to handle more variations
                opts = yaml.load(line.strip())
                for k, v in opts.items():
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
    """Converts a dict to a line-delimited string suitable for
    returning to the UI as the value of a textarea.
    """
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

import re
import dateutil.parser
from datetime import datetime


def testformat(s):
    """Parses date and returns a dict with the date string, format,
    and an error message if the date cannot be parsed.
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
        return {'text': s, 'format': dateformat}
    else:
        return {'text': s, 'format': 'unknown', 'error': error}


def textarea2datelist(textarea):
    """Converts a textarea string into a list of date dicts.
    """

    lines = textarea.replace('-\n', '- \n').split('\n')
    all_lines = []
    for line in lines:
        line = line.replace(', ', ',')
        dates = line.split(',')
        for item in dates:
            if re.search(' - ', item):  # Check for ' -'
                d = {'range': {'start': ''}}
                range = item.split(' - ')
                start = testformat(range[0])
                end = testformat(range[1])
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
    """Flattens the output of textarea2datelist() by removing 'text' and 'format' properties
    and replacing their container dicts with a simple date string.
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
    """Converts the output of flatten_datelist() to a line-delimited string suitable for
    returning to the UI as the value of a textarea.
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
