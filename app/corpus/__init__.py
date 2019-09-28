"""Corpus __init__.py."""

# import: standard
from datetime import datetime
import glob
import itertools
import json
import os
from pathlib import Path
from random import randint
import re
import shutil
import subprocess
import zipfile
# import: third-party
from bson import BSON
from bson import json_util
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, url_for, current_app, send_file, session
from jsonschema import validate, FormatChecker
import pymongo
from pymongo import MongoClient
import requests
import tabulator
from werkzeug.utils import secure_filename
import yaml
# import: app
from app.corpus.helpers import methods  # pylint: disable=cyclic-import
from app.corpus.helpers.query import Query, paginate
from app import db  # pylint: disable=cyclic-import
corpus_db = db.client[db.corpus]['Corpus']
JSON_UTIL = json_util.default

# Database info should be imported by the code above,
# but the code below is retained in case it needs
# to be activated for testing.

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
# client = MongoClient('mongodb://localhost:27017')
# db = client.we1s
# corpus_db = db.Corpus
# client = MongoClient('mongodb://mongo:27017')
# DB has one collection, so treat it as the whole DB
# corpus_db = client.Corpus.Corpus

corpus = Blueprint('corpus', __name__, template_folder='corpus')

# ----------------------------------------------------------------------------#
# Constants.
# ----------------------------------------------------------------------------#

ALLOWED_EXTENSIONS = ['xlsx']
# Horrible hack to get the instance path from out of context
root_path = corpus.root_path.replace('\\', '/').split('/')
del root_path[-2:]
instance_path = '/'.join(root_path) + '/instance'
TEMP_DIR = os.path.join(instance_path, 'temp')
IMPORT_SERVER_DIR = os.path.join(instance_path, 'fake_server_dir')
TRASH_DIR = os.path.join(instance_path, 'trash')

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@corpus.route('/')
def index():
    """Corpus index page."""
    scripts = ['js/parsley.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/corpus/corpus.js']
    breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}]
    return render_template('corpus/index.html', scripts=scripts, breadcrumbs=breadcrumbs)


@corpus.route('/create', methods=['GET', 'POST'])
def create():
    """Create manifest page."""
    # , 'js/corpus/datehandler.js'
    scripts = ['js/parsley.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/corpus/corpus.js']
    styles = ['css/jquery-ui.css']
    breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/create', 'label': 'Create Collection'}]
    templates_dir = os.path.join(current_app.root_path, 'templates')
    with open(os.path.join(templates_dir, 'corpus/template_config.yml'), 'r') as stream:
        templates = yaml.load(stream)
    return render_template('corpus/create.html', scripts=scripts, styles=styles, templates=templates, breadcrumbs=breadcrumbs)


@corpus.route('/create-manifest', methods=['GET', 'POST'])
def create_manifest():
    """Ajax route for creating manifests."""
    errors = []
    data = request.json
    # Get a top-level collection from the metapath
    parts = data['metapath'].split(',')
    if parts[0] == 'Corpus':
        del parts[0]
    doc_collection = parts[0]
    # Set name and path by branch
    if data['nodetype'] == 'collection':
        # Ensure that the metapath begins with 'Corpus'
        data['metapath'] = 'Corpus' + ','.join(parts)
        # try:
        #     assert data['metapath'] == 'Corpus'
        # except:
        #     errors.append('The <code>metapath</code> for a collection must be "Corpus".')
    elif data['nodetype'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
        data['name'] = data['nodetype']
    else:
        pass
    if not data['metapath'].startswith('Corpus'):
        data['metapath'] = 'Corpus,' + data['metapath']
    data['metapath'] = data['metapath'].strip(',')
    # Remove empty values
    manifest = {}
    for key, value in data.items():
        if value != '':
            manifest[key] = value
    if 'OCR' in manifest.keys() and manifest['OCR'] == "on":
        manifest['OCR'] = True
    nodetype = manifest.pop('nodetype', None)

    # Validate the resulting manifest
    # print(json.dumps(manifest, indent=2, sort_keys=False))
    if methods.validate_manifest(manifest, nodetype, skip=True) is True:
        database_errors = methods.create_record(manifest, doc_collection)
        errors = errors + database_errors
    else:
        msg = '''A valid manifest could not be created with the
        data supplied. Please check your entries against the
        <a href="/schema" target="_blank">manifest schema</a>.'''
        errors.append(msg)

    manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
    if errors:
        error_str = '<ul>'
        for item in errors:
            error_str += '<li>' + item + '</li>'
        error_str += '</ul>'
    else:
        error_str = ''
    response = {'manifest': manifest, 'errors': error_str}
    return json.dumps(response)


def get_default_property(template, prop):
    """Return the first column key in the template for the specified property."""
    for tab in [template['collection-template'][0]['required'], template['collection-template'][1]['optional']]:
        for item in tab:
            if item['name'] == prop:
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


# @corpus.route('/display/<name>')
# def display(name):
@corpus.route('/display')
def display():
    """Page for displaying Corpus manifests."""
    scripts = ['js/parsley.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/corpus/corpus.js']
    breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/display', 'label': 'Display Collection'}]
    errors = []
    manifest = {}
    try:
        collection = request.args.get('c')
        doc_id = request.args.get('_id')
        collection_db = db.client[db.corpus][collection]
        manifest = collection_db.find_one({'_id': ObjectId(doc_id)})
        if manifest['metapath'] == 'Corpus':
            nodetype = 'collection'
        elif manifest['name'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
            nodetype = manifest['name'].lower()
        else:
            nodetype = 'branch'
        templates_dir = os.path.join(current_app.root_path, 'templates')
        with open(os.path.join(templates_dir, 'corpus/template_config.yml'), 'r') as stream:
            templates = yaml.load(stream)
        # Reshape Lists
        for key, value in manifest.items():
            # The property is a list
            if isinstance(value, list):
                manifest[key] = reshape_list(key, value, templates)

        # Make sure the manifest has all template properties
        templates = templates[nodetype + '-template']
        opts = [templates[0]['required'], templates[1]['optional']]
        for opt in opts:
            for prop in opt:
                if prop['name'] not in manifest and prop['fieldtype'] == 'text':
                    manifest[prop['name']] = ''
                if prop['name'] not in manifest and prop['fieldtype'] == 'textarea':
                    manifest[prop['name']] = ['']
    except:
        nodetype = None
        collection = None
        doc_id = None
        templates = yaml.load('')
        errors.append('Unknown Error: The manifest does not exist or could not be loaded.')

    return render_template('corpus/display.html', scripts=scripts,
                           breadcrumbs=breadcrumbs, manifest=manifest,
                           errors=errors, nodetype=nodetype, doc_id=doc_id,
                           template=templates, collection=collection)


@corpus.route('/update-manifest', methods=['GET', 'POST'])
def update_manifest():
    """Ajax route for updating manifests."""
    errors = []
    data = request.json
    # Set name and path by branch
    if data['metapath'] == 'Corpus':
        data['nodetype'] = 'collection'
    elif data['name'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
        data['nodetype'] = data['name']
        data['metapath'] = 'Corpus,' + data['metapath']
    else:
        data['nodetype'] = 'branch'
        data['metapath'] = 'Corpus,' + data['metapath']
    data['metapath'] = data['metapath'].replace('Corpus,Corpus,', 'Corpus,').strip(',')
    # Remove empty values
    manifest = {}
    for key, value in data.items():
        if value != '':
            manifest[key] = value
    nodetype = manifest.pop('nodetype', None)
    if 'OCR' in manifest.keys() and manifest['OCR'] == "on":
        manifest['OCR'] = True
    # Validate the resulting manifest and update the record
    doc_collection = data['doc_collection']
    doc_id = data['doc_id']
    database_errors = methods.update_record(manifest, nodetype, doc_collection, doc_id)
    errors = errors + database_errors

    manifest = json.dumps(manifest, indent=2, sort_keys=False)
    print(manifest)
    if errors:
        error_str = '<ul>'
        for item in errors:
            error_str += '<li>' + item + '</li>'
        error_str += '</ul>'
    else:
        error_str = ''
    response = {'manifest': manifest, 'errors': error_str}
    return json.dumps(response)


@corpus.route('/send-export', methods=['GET', 'POST'])
def send_export():
    """Ajax route to process user export options and write the export files to the temp folder."""
    data = request.json
    print(data)
    doc_id = data.pop('doc_id')
    doc_collection = data.pop('doc_collection')
    # The user only wants to print the manifest
    if data['exportoptions'] == ['manifestonly']:
        query = {'_id': ObjectId(doc_id)}
        # query = {'name': data['name'], 'metapath': data['metapath']}
        try:
            result = db.client[db.corpus][doc_collection].find_one(query)
            assert result is not None
            manifest = {}
            for key, value in result.items():
                if value != '' and value != []:
                    manifest[key] = value
            manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
            filename = data['name'] + '.json'
            doc = filename
            methods.make_dir(TEMP_DIR)
            filepath = os.path.join(TEMP_DIR, filename)
            with open(filepath, 'w') as f:
                f.write(manifest)
            return json.dumps({'filename': doc})
        except:
            return json.dumps({'errors': ['Could not find the manifest in the database.']})
    # The user wants a zip of multiple data documents
    else:
        # Get the exportoptions with the correct case
        methods.make_dir(os.path.join(TEMP_DIR, 'Corpus'))
        name = data['name']
        metapath = data['metapath']
        # Ensures that there is a Corpus and collection folder with a collection manifest
        methods.make_dir(os.path.join(TEMP_DIR, 'Corpus'))
        if metapath == 'Corpus':
            collection = name
        else:
            collection = metapath.split(',')[2]
        corpus_dir = os.path.join(TEMP_DIR, 'Corpus')
        methods.make_dir(os.path.join(corpus_dir, collection))
        # result = corpus_db.find_one({'metapath': metapath, 'name': collection})
        # result = corpus_db.find_one({'metapath': metapath})
        result = corpus_db[doc_collection].find_one({'_id': ObjectId(doc_id)})
        # assert result is not None
        manifest = {}
        for key, value in result.items():
            if value != '' and value != []:
                manifest[key] = value
        manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
        filename = name + '.json'
        filepath = os.path.join(corpus_dir, filename)
        with open(filepath, 'w') as f:
            f.write(manifest)
        exportoptions = []
        exportopts = [x.replace('export', '') for x in data['exportoptions']]
        exclude = []
        options = ['Corpus', 'RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']
        if not metapath.startswith('Corpus,'):
            metapath = 'Corpus,' + metapath
        for option in options:
            if option.lower() in exportopts:
                exportoptions.append(option)
            else:
                exclude.append('Corpus' + ',' + name + ',' + option + ',.*')
        # We have a path and a list of metapaths to exclude
        excluded = '|'.join(exclude)
        excluded = re.compile(excluded)
        regex_path = re.compile(metapath + name + ',.*')
        result = corpus_db[doc_id].find(
            {'metapath': {
                '$regex': regex_path,
                '$not': excluded
            }}
        )
        for item in list(result):
            # Handle schema node manifests
            path = item['metapath'].replace(',', '/')
            if item['name'] in exportoptions:
                folder_path = os.path.join(path, item['name'])
                methods.make_dir(os.path.join(TEMP_DIR, folder_path))
                folder = os.path.join(TEMP_DIR, path)
                doc = item['name'] + '.json'
            # Handle data and branches
            else:
                # If the document has content, just give it a filename
                try:
                    assert item['content']
                    doc = item['name'] + '.json'
                    folder = os.path.join(TEMP_DIR, path)
                    methods.make_dir(folder)
                # Otherwise, use it to create a folder with a manifest file
                except:
                    path = os.path.join(path, item['name'])
                    folder = os.path.join(TEMP_DIR, path)
                    methods.make_dir(folder)
                    doc = item['name'] + '.json'
            filepath = os.path.join(folder, doc)
            output = json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL)
            with open(filepath, 'w') as f:
                f.write(output)
        # Zip up the file structure
        try:
            source_dir = os.path.join(TEMP_DIR, 'Corpus')
            doc = 'Corpus.zip'
            methods.zipfolder(source_dir, source_dir)
            return json.dumps({'filename': doc})
        except:
            return json.dumps({'errors': ['Could not make zip archive.']})


@corpus.route('/download-export/<filename>', methods=['GET', 'POST'])
def download_export(filename):
    """Ajax route to trigger download and empty the temp folder."""
    from flask import make_response
    filepath = os.path.join(TEMP_DIR, filename)
    # Can't get Firefox to save the file extension by any means
    with open(filepath, 'rb') as f:
        response = make_response(f.read())
    os.remove(filepath)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
    # As a precaution, empty the temp folder
    shutil.rmtree(TEMP_DIR)
    methods.make_dir(TEMP_DIR)
    return response


@corpus.route('/search1', methods=['GET', 'POST'])
def search1():
    """Page for searching Corpus manifests."""
    scripts = ['js/parsley.min.js', 'js/jquery.twbsPagination.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/corpus/corpus.js']

    breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/search', 'label': 'Search Collections'}]
    if request.method == 'GET':
        return render_template('corpus/search.html', scripts=scripts, breadcrumbs=breadcrumbs)
    if request.method == 'POST':
        result, num_pages, errors = methods.search_collections(request.json)
        if result == []:
            errors.append('No records were found matching your search criteria.')
        return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors})


@corpus.route('/search', methods=['GET', 'POST'])
def search():
    """Experimental Page for searching Corpus manifests."""
    scripts = ['js/parsley.min.js',
               'js/query-builder.standalone.js',
               'js/moment.min.js',
               'js/jquery.twbsPagination.min.js',
               'js/jquery-sortable-min.js',
               'js/jquery-ui.js',
               'js/corpus/corpus.js',
               'js/corpus/search.js',
               'js/bootstrap-select-1.13.9/js/bootstrap-select.min.js'
               ]

    styles = ['css/query-builder.default.css', 'js/bootstrap-select-1.13.9/css/bootstrap-select.css']
    breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/search', 'label': 'Search Collections'}]
    if request.method == 'GET':
        collections = db.client[db.corpus].list_collection_names()
        return render_template('corpus/search.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs, collections=collections)
    if request.method == 'POST':
        # Default settings
        collection_list = db.client[db.corpus].list_collection_names()
        errors = []
        query = {}
        page_size = 10
        page_num = 1
        num_pages = 1
        pages = []
        limit = 0
        sortby = [['name', 'ASC']]
        projection = ['name', '_id']
        head = None
        filters = None
        # Assemble request data
        if request.json['collections']:
            collection_list = request.json['collections']
            if isinstance(collection_list, str):
                collection_list = [collection_list]
        if request.json['page']:
            page_num = request.json['page']
        if request.json['query']:
            query = request.json['query']
        if request.json['advancedOptions']['limit']:
            limit = request.json['advancedOptions']['limit']
        if request.json['advancedOptions']['sort']:
            sortby = request.json['advancedOptions']['sort']
        else:
            sortby = None
        if request.json['advancedOptions']['show_properties'] != []:
            projection = request.json['advancedOptions']['show_properties']
            original_projection = projection.copy()
        else:
            projection = None

        # Query the entire database
        query = Query(db.client, db.corpus, collection_list, query, projection=projection, sortby=sortby, limit=limit, head=head, filters=filters)
        records = query.get_records(sortby=sortby, projection=projection, filters=query.filters)

        # Check whether records can be returned
        if records == []:
            errors.append('No records were found matching your search criteria.')
        else:
            # Paginate the result
            pages, num_pages = paginate(records, page_size, None)
            # print('Number of Pages: ' + str(num_pages) + '\n')

            # Get just the requested page
            records = pages[page_num]
            # Remove None at the end
            records = [record for record in records if record is not None]

            # Remove the _id field if not requested
            if '_id' not in original_projection:
                for k, _ in enumerate(records):
                    if records[k] is None:
                        del records[k]
                    # else:
                    #     del records[k]['_id']

        # Return the response
        response = {
            'response': records,
            'errors': errors,
            'num_pages': num_pages,
            'pages': pages,
            'large_query': query.large_query
        }
        return json.dumps(response, default=JSON_UTIL)


@corpus.route('/export-search', methods=['GET', 'POST'])
def export_search():
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
        result, _, errors = methods.search_corpus(query, limit, paginated, page, show_properties, sorting)
        if not result:
            errors.append('No records were found matching your search criteria.')
        # Need to write the results to temp folder
        for item in result:
            filename = item['name'] + '.json'
            filepath = os.path.join(TEMP_DIR, filename)
            with open(filepath, 'w') as f:
                f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
        # Need to zip up multiple files
        if len(result) > 1:
            filename = 'search_results.zip'
            methods.zipfolder(TEMP_DIR, 'search_results')
        return json.dumps({'filename': filename, 'errors': errors}, default=JSON_UTIL)


@corpus.route('/delete-manifest', methods=['GET', 'POST'])
def delete_manifest():
    """Ajax route for deleting manifests."""
    errors = []
    name = request.json['name']
    metapath = request.json['metapath']
    doc_id = request.json['doc_id']
    doc_collection = request.json['doc_collection']
    msg = methods.delete_collection(name, metapath, doc_id, doc_collection)
    if msg != 'success':
        errors.append(msg)
    return json.dumps({'errors': errors})


@corpus.route('/import', methods=['GET', 'POST'])
def import_data():
    """Page for importing manifests."""
    scripts = ['js/corpus/dropzone.js',
               'js/parsley.min.js',
               'js/corpus/corpus.js',
               'js/corpus/upload.js']
    # Start an import session on page load
    token = datetime.now().strftime('%Y%m%d_') + str(randint(0, 99))
    session['IMPORT_DIR'] = os.path.join(TEMP_DIR, token).replace('\\', '/')

    result = get_server_files()

    # Needs better error handling
    if result != 'error':
        server_files = result
    breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/import', 'label': 'Import Collection Data'}]
    return render_template('corpus/import.html', scripts=scripts,
                           breadcrumbs=breadcrumbs, server_files=server_files,
                           session_token=token)


def listdir(path):
    """Replace the os directory list function with one that ignores hidden files."""
    return glob.glob(os.path.join(path, '*'))


def get_server_files():
    """Get the files available for import from the server."""
    file_list = listdir(IMPORT_SERVER_DIR)
    # file_list = ['myfile1.json', 'myfile2.json', 'myfile3.json', 'myzipfile1.zip']
    return file_list


@corpus.route('/import-server-file', methods=['GET', 'POST'])
def import_server_data():
    """Import files staged by the task manager."""
    errors = []
    collection = request.json['collection']
    category = request.json['category']
    branch = request.json['branch']
    filename = request.json['filename']
    # Construction a metapath
    if collection == '':
        errors.append('Please indicate the name of the collection where you want to import the data.')
    else:
        metapath = collection + ',' + category
    if branch != '':
        metapath = metapath + ',' + branch
    # If the user's selected filename is in the server import directory
    if filename in listdir(IMPORT_SERVER_DIR):
        # Iterate through json files in zip archive
        if filename.endswith('.zip'):
            with zipfile.ZipFile(os.path.join(IMPORT_SERVER_DIR, filename)) as z:
                for fn in z.namelist():
                    # We're trusting that the zip archive contains
                    # only valid manifest files and no folders.
                    with z.open(fn) as f:
                        manifest = json.loads(f.read())
                    # Now we try to insert the manifest in the database
                    if corpus_db.find({'name': manifest['name'], 'metapath': metapath}).count > 0:
                        msg = 'A collection already exists containing a manifest with the name <code>' + manifest['name'] + '</code>.'
                        errors.append(msg)
                    else:
                        corpus_db.insert_one(manifest)
        else:
            # Import a single json manifest
            try:
                with open(os.path.join(IMPORT_SERVER_DIR, filename), 'r') as f:
                    manifest = json.loads(f.read())
                # Now we try to insert the manifest in the database
                if corpus_db.find({'name': manifest['name'], 'metapath': metapath}).count() > 0:
                    msg = 'A collection already exists containing a manifest with the name <code>' + manifest['name'] + '</code>.'
                    errors.append(msg)
                else:
                    # corpus_db.insert_one(manifest)
                    pass
                # Move the file to the trash folder (ensuring it is unique)
                source = os.path.join(IMPORT_SERVER_DIR, filename)
                if filename in listdir(TRASH_DIR):
                    filename = datetime.now().strftime('%Y%m%d%H%M%S_') + filename
                destination = os.path.join(TRASH_DIR, filename)
                shutil.move(source, destination)
            except:
                errors.append('<p>The file could not be read or the manifest could not be inserted in the database.</p>')
    else:
        errors.append('The filename could not be found on the server.')
    if errors:
        response = json.dumps({'result': 'fail', 'errors': errors})
    else:
        response = json.dumps({'result': 'success', 'errors': []})
    return response


@corpus.route('/refresh-server-imports', methods=['GET', 'POST'])
def refresh_server_imports():
    """Refresh the table of files staged for import on the front end."""
    file_list = get_server_files()
    return json.dumps({'file_list': file_list})


@corpus.route('/remove-file', methods=['GET', 'POST'])
def remove_file():
    """Ajax route triggered when a file is deleted from the file uploads table.

    This function removes the file from the imports folder but does not remove
    it from the database.
    """
    if request.method == 'POST':
        if os.path.isfile(os.path.join(session['IMPORT_DIR'], request.json['filename'])):
            source = os.path.join(session['IMPORT_DIR'], request.json['filename'])
            destination = os.path.join(session['TRASH_DIR'], request.json['filename'])
            os.rename(source, destination)
        return json.dumps({'response': 'success'})


@corpus.route('/remove-all-files', methods=['GET', 'POST'])
def remove_all_files():
    """Ajax route triggered when all files are deleted from the file uploads table.

    This function deletes the import session folder but does not remove any items
    already added to the database.
    """
    # If there is a session import folder
    if os.path.isdir(session['IMPORT_DIR']):
        # Move each file to the trash folder (ensuring it is unique)
        for filename in listdir(session['IMPORT_DIR']):
            if filename in listdir(TRASH_DIR):
                filename = datetime.now().strftime('%Y%m%d%H%M%S_') + filename
            source = os.path.join(session['IMPORT_DIR'], filename)
            destination = os.path.join(TRASH_DIR, filename)
            shutil.move(source, destination)
        # Delete the session import folder
        shutil.rmtree(session['IMPORT_DIR'])
        response = json.dumps({'response': 'success'})
    else:
        response = json.dumps({'response': 'session is empty'})
    return response


@corpus.route('/save-upload', methods=['GET', 'POST'])
def save_upload():
    """Ajax route to create a manifest for each uploaded file and insert it in the database."""
    if request.method == 'POST':
        print('Working session folder: ' + session['IMPORT_DIR'])
        errors = []
        # Make sure the collection exists before handling form data
        try:
            result = list(corpus_db.find({'name': request.json['collection']}))
            assert result != []
            # Handle the form data
            exclude = ['branch', 'category', 'collection']
            node_metadata = {}
            for key, value in request.json.items():
                if key not in exclude and value != '' and value != []:
                    node_metadata[key] = value
            # Set the name and metapath
            if request.json['collection'].startswith('Corpus,'):
                collection = request.json['collection']
            else:
                collection = 'Corpus,' + request.json['collection']
        except:
            errors.append('The specified collection does not exist in the database. Check your entry or <a href="/corpus/create">create a collection</a> before importing data.')

        if not errors:
            # Set the name and path for the new manifest
            node_metadata = {}
            if request.json['branch'] != '':
                node_metadata['name'] = request.json['branch']
                node_metadata['metapath'] = collection + ',' + request.json['category']
            else:
                node_metadata['name'] = request.json['category']
                node_metadata['metapath'] = collection

        # If the specified metapath does not exist, create it
        if not errors:
            parent = list(corpus_db.find({'name': node_metadata['name'], 'metapath': node_metadata['metapath']}))
            if not parent:
                try:
                    corpus_db.insert_one(node_metadata)
                except:
                    errors.append('<p>The specified metapath does not exist and could not be created.</p>')

        # Now create a data manifest for each file and insert it
        if not errors:
            for filename in listdir(session['IMPORT_DIR']):
                print('Creating manifest for ' + filename)
                if filename.endswith('.json'):
                    filepath = os.path.join(session['IMPORT_DIR'], filename)
                    metapath = node_metadata['metapath'] + ',' + node_metadata['name']
                    manifest = {'name': os.path.splitext(filename)[0], 'namespace': 'we1sv2.0', 'metapath': metapath}
                    try:
                        with open(filepath, 'rb') as f:
                            doc = json.loads(f.read())
                            for key, value in doc.items():
                                if key not in ['name', 'namespace', 'metapath']:
                                    manifest[key] = value
                    except:
                        errors.append('<p>The file <code>' + filename + '</code> could not be loaded or it did not have a <code>content</code> property.</p>')
                    # Validate the manifest before inserting
                    schema_file = 'https://raw.githubusercontent.com/whatevery1says/manifest/master/schema/v2.0/Corpus/Data.json'
                    schema = json.loads(requests.get(schema_file).text)
                    print(manifest['name'])
                    print(manifest['metapath'])
                    try:
                        methods.validate(manifest, schema, format_checker=FormatChecker())
                        result = methods.create_record(manifest, collection)
                        errors = errors + result
                        print(errors)
                    except:
                        errors.append('<p>A valid manifest could not be created from the file <code>' + filename + '</code> or the manifest could not be added to the database due to an unknown error.</p>')
                else:
                    errors.append('<p>The file <code>' + filename + '</code> is an invalid format.</p>')

        # We're done. Delete the import directory
        shutil.rmtree(session['IMPORT_DIR'])

        # Refresh the session
        token = datetime.now().strftime('%Y%m%d_') + str(randint(0, 99))
        session['IMPORT_DIR'] = os.path.join(TEMP_DIR, token).replace('\\', '/')

        if not errors:
            response = json.dumps({'result': 'success', 'session_token': 'token'})
        else:
            response = json.dumps({'errors': errors})
        return response


@corpus.route('/upload/', methods=['GET', 'POST'])
def upload():
    """Ajax route saves each file uploaded by the import function to the uploads folder."""
    errors = []
    if request.method == 'POST':
        # Create a session import directory if it does not exist
        if not os.path.exists(session['IMPORT_DIR']):
            os.makedirs(session['IMPORT_DIR'])

        for file in request.files.getlist('file'):
            # Unzip .zip files
            if file.filename.endswith('.zip'):
                print('Processing zip file')
                try:
                    filepath = os.path.join(session['IMPORT_DIR'], file.filename)
                    with zipfile.ZipFile(filepath) as zf:
                        zf.extractall(session['IMPORT_DIR'])
                    print('Zip file extracted to ' + session['IMPORT_DIR'])
                    # Move the files up to the main uploads folder
                    extracted_folder = os.path.splitext(file.filename)[0]
                    print('Extracted folder: ' + extracted_folder)
                    sourcepath = os.path.join(session['IMPORT_DIR'], extracted_folder)
                    for extracted_file in listdir(sourcepath):
                        if extracted_file.endswith('.json'):
                            shutil.move(os.path.join(sourcepath, extracted_file), os.path.join(session['IMPORT_DIR'], extracted_file))
                    # Remove the zip archive and empty folder
                    os.remove(filepath)
                    os.rmdir(sourcepath)
                except:
                    errors.append('<p>Unknown Error: Could not process the zip file <code>' + file.filename + '</code>.</p>')
            # Handle .json files
            elif file.filename.endswith('.json'):
                try:
                    filename = secure_filename(file.filename)
                    file_to_save = os.path.join(session['IMPORT_DIR'], filename)
                    file_to_save = os.path.join('app', file_to_save)
                    file.save(file_to_save)
                except:
                    errors.append('<p>Unknown Error: Could not save the file <code>' + filename + '</code>.</p>')
            else:
                errors.append('<p>The file <code>' + file.filename + '</code> has an invalid file type.</p>')
        if errors == []:
            response = {'response': 'File(s) saved successfully.'}
        else:
            response = {'errors': errors}
        return json.dumps(response)


@corpus.route('/clear/<metapath>')
def clear(metapath):
    """Go to this page to quickly empty the database of all records along the designated metapath.

    Use the metapath 'all' for delete all records in the database. Disable this for production.
    """
    try:
        if metapath == 'all':
            corpus_db.delete_many({})
            response = 'All records in Corpus database were deleted.'
        else:
            metapath = re.compile('^' + metapath)
            corpus_db.delete_many({'metapath': {'$regex': metapath}})
            response = 'Delete all records under ' + metapath + '.'
    except:
        response = 'There was an error. No records were deleted.'
    return response
