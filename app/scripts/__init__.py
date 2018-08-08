"""Scripts __init__.py.
Note: This module has not yet been developed. This file is a placeholder.
"""

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


JSON_UTIL = json_util.default

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
scripts_db = db.Scripts
corpus_db = db.Corpus

scripts = Blueprint('scripts', __name__, template_folder='scripts')

# from app.scripts.helpers import methods as methods

# ----------------------------------------------------------------------------#
# Constants.
# ----------------------------------------------------------------------------#


ALLOWED_EXTENSIONS = ['zip']

# ----------------------------------------------------------------------------#
# Model.
# ----------------------------------------------------------------------------#


class Script():
    """Model a script or tool.

    Parameters:
    - manifest: dict containing form data for the script or tool manifest
    - query: dict containing the database query
    - action: the database action to be taken: "insert" or "update"

    Returns a JSON object: `{'response': 'success|fail', 'errors': []}`

    """

    def __init__(self, manifest, query, action):
        """Initialize the object."""
        self.action = action
        self.manifest = manifest
        self.query = json.loads(query)
        self.name = manifest['name']
        self.filename = manifest['name'] + '.zip'

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@scripts.route('/')
def index():
    """Scripts index page."""
    script_list = ['js/corpus/dropzone.js', 'js/scripts/scripts.js', 'js/scripts/upload.js', 'js/dateformat.js', 'js/jquery-ui.js']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}]
    return render_template('scripts/index.html', scripts=script_list, breadcrumbs=breadcrumbs)


@scripts.route('/create', methods=['GET', 'POST'])
def create():
    """Create/update script or tool page."""
    script_list = ['js/corpus/dropzone.js', 'js/parsley.min.js', 'js/moment.min.js', 'js/scripts/scripts.js', 'js/scripts/upload.js', 'js/dateformat.js', 'js/jquery-ui.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}, {'link': '/scripts/create', 'label': 'Create/Update Script'}]
    with open('app/templates/scripts/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    return render_template('scripts/create.html', scripts=script_list, styles=styles, templates=templates, breadcrumbs=breadcrumbs)


@scripts.route('/display/<name>', methods=['GET', 'POST'])
def display(name):
    """Display script or tool page."""
    script_list = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery-sortable-min.js', 'js/scripts/scripts.js', 'js/scripts/search.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}, {'link': '/scripts/create', 'label': 'Display Script'}]
    errors = []
    manifest = {}
    with open('app/templates/scripts/template_config.yml', 'r') as stream:
        templates = yaml.load(stream)
    try:
        result = scripts_db.find({'name': name})
        assert result is not None
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
    except AssertionError:
        errors.append('Unknown Error: The script or tool does not exist or could not be loaded.')
    return render_template('scripts/display.html', scripts=script_list,
                           breadcrumbs=breadcrumbs, manifest=manifest,
                           errors=errors, templates=templates, styles=styles)


@scripts.route('/search', methods=['GET', 'POST'])
def search():
    """Experimental Page for searching Scripts manifests."""
    script_list = ['js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/scripts/scripts.js', 'js/jquery-sortable-min.js', 'js/scripts/search.js', 'js/dateformat.js', 'js/jquery-ui.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/scripts', 'label': 'Scripts'}, {'link': '/scripts/search', 'label': 'Search Scripts'}]
    if request.method == 'GET':
        return render_template('scripts/search.html', scripts=script_list, styles=styles, breadcrumbs=breadcrumbs)
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
        result, _, errors = search_scripts(query, limit, paginated, page, show_properties, sorting)
        if not result:
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
    """Import scripts."""
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
            assert list(result)
            scripts_db.insert_one(manifest)
        except AssertionError:
            errors.append('The database already contains a script or tool with the same name.')
        # Create a response to send to the browser
        if errors == []:
            del manifest['content']
            response = {'result': 'success', 'manifest': manifest, 'errors': errors}
        else:
            response = {'result': 'fail', 'manifest': manifest, 'errors': errors}
        return json.dumps(response, indent=2, sort_keys=False, default=JSON_UTIL)


def load_saved_datapackage(manifest, zip_filepath, scripts_dir, workspace_dir):
    """Load saved datapackage."""
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
    """Make new datapackage."""
    # Make sure the Corpus query returns results
    errors = []
    try:
        result = list(corpus_db.find(data['db_query']))
        assert result
    except AssertionError:
        errors.append('<p>Could not find any Corpus data. Please test your query.</p>')
    if result:
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


# ----------------------------------------------------------------------------#
# Helpers.
# ----------------------------------------------------------------------------#


def empty_tempfolder():
    """Empty the temporary folder."""
    temp_folder = Path(os.path.join('app', current_app.config['TEMP_FOLDER']))
    shutil.rmtree(temp_folder)
    temp_folder.mkdir(parents=True, exist_ok=True)


def search_scripts(query, limit, paginated, page, show_properties, sorting):
    """Use the query generated in /search and returns the search results."""
    page_size = 10
    errors = []
    if list(scripts_db.find()):
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
    """Take a list of paginated results form `paginate()` and return a single page from the list."""
    try:
        return pages[page - 1]
    except:
        print('The requested page does not exist.')


def paginate(iterable, page_size):
    """Return a generator with a list sliced into pages by the designated size.

    If the generator is converted to a list called `pages`, and individual page can
    be called with `pages[0]`, `pages[1]`, etc.
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

    Duplicates method in Script class.

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
    """Generate a script manifest from a zipped datapackage.

    The zip file is embedded in the `content` property, so the
    script manifest is read for insertion in the database.
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
        manifest['metapath'] = 'Scripts'
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
        return {'text': s, 'format': dateformat}
    else:
        return {'text': s, 'format': 'unknown', 'error': error}


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
                except AssertionError:
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
