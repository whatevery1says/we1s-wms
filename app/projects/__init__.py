import os, tabulator, itertools, requests, json, re, zipfile, shutil
import uuid
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from jsonschema import validate, FormatChecker

# For various solutions to dealing with ObjectID, see
# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
# If speed becomes an issue: https://github.com/mongodb-labs/python-bsonjs
from bson import BSON, Binary, json_util, ObjectId
JSON_UTIL = json_util.default

from jsonschema import validate, FormatChecker
from flask import Blueprint, render_template, request, url_for, current_app, send_file
from werkzeug.utils import secure_filename

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
projects_db = db.Projects
corpus_db = db.Corpus

projects = Blueprint('projects', __name__, template_folder='projects')

# from app.projects.helpers import methods as methods
from app.projects.helpers import workspace as workspace

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
    """Models a project. Parameters:
    manifest: dict containing form data for the project manifest
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
        """Test whether the project already exists in the database."""
        test = projects_db.find_one({'name': self.name})
        if test != None:
            return True
        else:
            return False

    def insert(self):
        """Insert a project in the database."""
        try:
            # Create the datapackage and add it to the manifest
            content, errors, key = self.make_datapackage()
            self.manifest['content'] = content
            # Insert the manifest into the database
            projects_db.insert_one(self.manifest)
            empty_tempfolder(key)
            return {'result': 'success', 'errors': errors}
        except:
            msg = """An unknown error occurred when trying to
            insert the project into the database."""
            return {'result': 'fail', 'errors': [msg]}

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
            except pymongo.errors.PyMongoError as e:
                print(e.__dict__.keys())
                # print(e._OperationFailure__details)
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
            except pymongo.errors.PyMongoError as e:
                print(e.__dict__.keys())
                # print(e._OperationFailure__details)
                msg = 'Unknown Fluff: The record for <code>name</code> <strong>' + self.name + '</strong> could not be updated.'
                errors.append(msg)
                return {'result': 'fail', 'errors': errors}


    def make_datapackage(self):
        """Create a project folder containing a data package, then
        make a zip archive of the folder. Returns a binary of the
        zip archive, a list of errors, and the key to the location
        of the archive in the temp folder."""
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

        # Create a unique folder in /workspace/temp and save the datapackage to it
        # temp_folder = os.path.join('app', current_app.config['TEMP_FOLDER'])
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
        if len(result) == 0:
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
        """Creates a zip archive of a source directory.

        Takes file paths for both the source directory
        and the output file.

        Note that the output filename should not have the
        .zip extension; it is added here.
        """
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


@projects.route('/')
def index():
    """Projects index page."""
    scripts = ['js/corpus/dropzone.js', 'js/projects/projects.js', 'js/projects/upload.js', 'js/jquery-ui.js', 'js/dateformat.js']
    breadcrumbs = [{'link': '/corpus', 'label': 'Scripts'}]
    return render_template('projects/index.html', scripts=scripts, breadcrumbs=breadcrumbs)


@projects.route('/create', methods=['GET', 'POST'])
def create():
    """Create/update project page."""
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery-sortable-min.js', 'js/projects/projects.js', 'js/projects/search.js', 'js/jquery-ui.js', 'js/dateformat.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/create', 'label': 'Create/Update Project'}]
    with open('app/templates/projects/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    return render_template('projects/create.html', scripts=scripts, styles=styles, templates=templates, breadcrumbs=breadcrumbs)


@projects.route('/display/<name>', methods=['GET', 'POST'])
def display(name):
    """Display project page."""
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery-sortable-min.js', 'js/projects/projects.js', 'js/projects/search.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/projects', 'label': 'Projects'}, {'link': '/projects/create', 'label': 'Display Project'}]
    errors = []
    manifest = {}
    with open('app/templates/projects/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    manifest = projects_db.find_one({'name': name})
    if manifest != None:
        try:
            del manifest['content']
            for key, value in manifest.items():
                if isinstance(value, list):
                    textarea = str(value)
                    textarea = dict2textarea(value)
                    manifest[key] = textarea
                else:
                    manifest[key] = str(value)
            manifest['metapath'] = 'Projects'
        except:
            errors.append('Unknown Error: Some items in the manifest could not be processed for display.')
    else:
        errors.append('Unknown Error: The project does not exist or could not be loaded.')
    return render_template('projects/display.html', scripts=scripts,
        breadcrumbs=breadcrumbs, manifest=manifest, errors=errors,
        templates=templates, styles=styles)


@projects.route('/test-query', methods=['GET', 'POST'])
def test_query():
    """Tests whether the project query returns results
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


@projects.route('/save-project', methods=['GET', 'POST'])
def save_project():
    """ Handles Ajax request data and instantiates the project class.
    Returns a dict containing a result (success or fail) and a list
    of errors."""
    query = request.json['query']
    action = request.json['action'] # insert or update
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
    # Instantiate a project object
    project = Project(manifest, query, action)
    # Reject an insert where the project name already exists
    if project.exists() and action == 'insert':
        print('Duplicate project cannot be inserted.')
        msg = 'This project name already exists in the database. Please choose another value for <code>name</code>.'
        response = {'result': 'fail', 'errors': [msg]}
    # Update the project
    elif project.exists() and action == 'update':
        print('Detected an update')
        response = project.update()
        # empty_tempfolder()
    # Insert a new project
    else:
        response = project.insert()
        # empty_tempfolder()
    # Return a success/fail flag and a list of errors to the browser
    return json.dumps(response)


@projects.route('/delete-project', methods=['GET', 'POST'])
def delete_project():
    manifest = request.json['manifest']
    print('Manifest to delete')
    print(manifest['name'])
    result = projects_db.delete_one({'name': manifest['name']})
    if result.deleted_count == 1:
        return json.dumps({'result': 'success', 'errors': []})
    else:
        errors = ['<p>Unknown error: The document could not be deleted.</p>']
        return json.dumps({'result': 'fail', 'errors': errors})


@projects.route('/export-project', methods=['GET', 'POST'])
def export_project():
    """ Handles Ajax request data and instantiates the project class.
    Returns a dict containing a result (success or fail) and a list
    of errors."""
    manifest = request.json['manifest']
    query = request.json['query']
    action = request.json['action'] # export
    # Instantiate a project object and make a data pacakge
    project = Project(manifest, query, action)
    content, errors, key = project.make_datapackage()
    if len(errors) == 0:
        response = {'result': 'success', 'key': key, 'errors': []}
    else:
        response = {'result': 'fail', 'errors': errors}
        empty_tempfolder(key)
    # Return a success/fail flag and a list of errors to the browser
    return json.dumps(response)


@projects.route('/download-export/<filepath>', methods=['GET', 'POST'])
def download_export(filepath):
    """ Ajax route to trigger download and empty the temp folder."""
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
    """ Experimental Page for searching Projects manifests."""
    scripts = ['js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/projects/projects.js', 'js/jquery-sortable-min.js', 'js/projects/search.js', 'js/dateformat.js', 'js/jquery-ui.js']
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
        return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)


@projects.route('/export-search-results', methods=['GET', 'POST'])
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
        result, num_pages, errors = search_projects(query, limit, paginated, page, show_properties, sorting)
        if len(result) == 0:
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
            assert len(list(result)) > 0
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


@projects.route('/launch-jupyter', methods=['GET', 'POST'])
def launch_jupyter():
    """ Creates a project folder on the server containing a
    project datapackage, along with any workspace templates.
    If successful, the Jupyter notebook is lost; otherwise,
    an error report is returned to the front end."""
    errors = []
    manifest = request.json['manifest']
    # The folder containing the notebook (e.g. we1s-topic-modeling)
    notebook_type = 'we1s-' + request.json['notebook']
    # Notebook to launch
    notebook_start = notebook_type + '/start'
    # Path to notebook
    path = manifest['name'] + '/Workspace/' + notebook_start + '.ipynb'
    # Fetch or create a datapackage based on the info received
    datapackage = workspace.Datapackage(manifest, WORKSPACE_PROJECTS)
    errors += datapackage.errors
    # If the datapackage has no errors, create the notebook
    if len(errors) == 0:
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
    if len(errors) > 0:
        return json.dumps({'result': 'fail', 'errors': errors})
    else:
        return json.dumps({'result': 'success', 'errors': []})


# ----------------------------------------------------------------------------#
# Helpers.
# ----------------------------------------------------------------------------#


def generate_key():
    uid = uuid.uuid4()
    dirlist = [item for item in os.listdir(WORKSPACE_TEMP) if os.path.isdir(os.path.join(WORKSPACE_TEMP, item))]
    if uid.hex not in dirlist:
        return uid.hex
    else:
        generate_key()


def empty_tempfolder(key):
    # temp_folder = Path(os.path.join('app', current_app.config['TEMP_FOLDER']))
    temp_folder = Path(os.path.join(WORKSPACE_TEMP, key))
    shutil.rmtree(temp_folder)
    temp_folder.mkdir(parents=True, exist_ok=True)


def search_projects(query, limit, paginated, page, show_properties, sorting):
    """Uses the query generated in /search and returns the search results.
    """
    page_size = 10
    errors = []
    if len(list(projects_db.find())) > 0:
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
                return page, num_pages, errors
            else:
                return result, 1, errors
        else:
            return [], 1, errors
    else:
        errors.append('The Projects database is empty.')
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

    Duplicates method in Project class.

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
    """Generates a project manifest from a zipped datapackage. The zip file is
    embedded in the `content` property, so the project manifest is read for
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
        manifest ['metapath'] = 'Projects'
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
                line = re.sub(pattern, '\n\\1', line) # Could be improved to handle more variations
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
            if re.search(' - ', item): # Check for ' -'
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
            dates.append(str(item)) # error dict is cast as a string
    return '\n'.join(dates)
