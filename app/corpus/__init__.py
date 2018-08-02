import os, tabulator, itertools, requests, json, re, zipfile, shutil
import subprocess
import yaml

# For various solutions to dealing with ObjectID, see
# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
# If speed becomes an issue: https://github.com/mongodb-labs/python-bsonjs
from bson import BSON
from bson import json_util
JSON_UTIL = json_util.default

from datetime import datetime
from random import randint
from pathlib import Path
from jsonschema import validate, FormatChecker
# from tabulator import Stream
# import pandas as pd
# from tableschema_pandas import Storage
from flask import Blueprint, render_template, request, url_for, current_app, send_file, session
from werkzeug.utils import secure_filename

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections" 
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
corpus_db = db.Corpus

corpus = Blueprint('corpus', __name__, template_folder='corpus')

from app.corpus.helpers import methods as methods

#----------------------------------------------------------------------------#
# Constants.
#----------------------------------------------------------------------------#

ALLOWED_EXTENSIONS = ['xlsx']
# Horrible hack to get the instance path from out of context
root_path = corpus.root_path.replace('\\', '/').split('/')
del root_path[-2:]
instance_path = '/'.join(root_path) + '/instance'
TEMP_DIR = os.path.join(instance_path, 'temp')
IMPORT_SERVER_DIR = os.path.join(instance_path, 'fake_server_dir')
TRASH_DIR = os.path.join(instance_path, 'trash')

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@corpus.route('/')
def index():
	"""Corpus index page."""
	scripts = ['js/corpus/corpus.js', 'js/jquery-ui.js', 'js/dateformat-corpus.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}]
	return render_template('corpus/index.html', scripts=scripts, breadcrumbs=breadcrumbs)


@corpus.route('/create', methods=['GET', 'POST'])
def create():
	"""Create manifest page."""
	scripts = ['js/parsley.min.js', 'js/corpus/corpus.js', 'js/jquery-ui.js', 'js/dateformat-corpus.js', 'js/moment.min.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/create', 'label': 'Create Collection'}]
	with open("app/templates/corpus/template_config.yml", 'r') as stream:
		templates = yaml.load(stream)
	return render_template('corpus/create.html', scripts=scripts, templates=templates, breadcrumbs=breadcrumbs)


@corpus.route('/create-manifest', methods=['GET', 'POST'])
def create_manifest():
	""" Ajax route for creating manifests."""
	errors = []
	data = request.json
	# data['namespace'] = 'we1sv2.0'
	# Set name and path by branch
	if data['nodetype'] == 'collection':
		try:
			assert data['metapath'] == 'Corpus'
		except:
			errors.append('The <code>metapath</code> for a collection must be "Corpus".')
	elif data['nodetype'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
		data['name'] = data['nodetype']
	else:
		pass
	if not data['metapath'].startswith('Corpus'):
		data['metapath'] = 'Corpus,' + data['metapath']
	data['metapath'] = data['metapath'].strip(',')
	# if not data['metapath'].endswith(','):
	# 	data['path'] += ','
	# Remove empty values
	manifest = {}
	for key, value in data.items():
		if value != '':
			manifest[key] = value
	# Handle dates
	# if 'date' in manifest.keys():
	# 	dates = manifest['date'].splitlines()
	# 	dates = [x.strip() for x in dates]
	# 	new_dates, error_list = methods.check_date_format(dates)
	# 	errors = errors + error_list
	# 	if new_dates  != []:
	# 		manifest['date'] = dates
	if 'created' in manifest.keys():
		created = methods.flatten_datelist(methods.textarea2datelist(manifest['created']))
		if isinstance(created, list) and len(created) == 1:
			created = created[0]

	if 'updated' in manifest.keys():
		updated = methods.flatten_datelist(methods.textarea2datelist(manifest['updated']))
		if isinstance(updated, list) and len(updated) == 1:
			updated = updated[0]

	# Handle other textarea strings
	list_props = ['sources', 'contributors', 'queryterms', 'processes', 'notes', 'keywords', 'licenses']
	prop_keys = {
		'sources': { 'main_key': 'title', 'valid_props': ['title', 'path', 'email'] },
		'contributors': { 'main_key': 'title', 'valid_props': ['title', 'email', 'path', 'role', 'group', 'organization'] },
		'licenses': { 'main_key': 'name', 'valid_props': ['name', 'path', 'title'] },
		'queryterms': { 'main_key': '', 'valid_props': [] },
		'processes': { 'main_key': '', 'valid_props': [] },
		'notes': { 'main_key': '', 'valid_props': [] },
		'keywords': { 'main_key': '', 'valid_props': [] }
	}
	for item in list_props:
		if item in manifest and manifest[item] != '':
			all_lines = methods.textarea2dict(item, manifest[item], prop_keys[item]['main_key'], prop_keys[item]['valid_props'])
			if all_lines[item] != []:
				manifest[item] = all_lines[item]
	nodetype = manifest.pop('nodetype', None)
	if 'OCR' in manifest.keys() and manifest['OCR'] == "on":
		manifest['OCR'] = True
	# Validate the resulting manifest
	if methods.validate_manifest(manifest, nodetype) == True:
		database_errors = methods.create_record(manifest)
		errors = errors + database_errors
	else:
		msg = '''A valid manifest could not be created with the 
		data supplied. Please check your entries against the 
		<a href="/schema" target="_blank">manifest schema</a>.''' 
		errors.append(msg)

	manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
	if len(errors) > 0:
		error_str = '<ul>'
		for item in errors:
			error_str += '<li>' + item + '</li>'
		error_str += '</ul>'
	else:
		error_str = ''
	response = {'manifest': manifest, 'errors': error_str}
	return json.dumps(response)


@corpus.route('/display/<name>')
def display(name):
	""" Page for displaying Corpus manifests."""
	scripts = ['js/parsley.min.js', 'js/corpus/corpus.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/display', 'label': 'Display Collection'}]
	errors = []
	manifest = {}
	try:
		result = corpus_db.find_one({'name': name})
		assert result != None
		for key, value in result.items():
			if isinstance(value, list):
				textarea = methods.dict2textarea(value)
				manifest[key] = textarea
			# if isinstance(value, list):
			# 	manifest[key] = []
			# 	for element in value:
			# 		if isinstance(element, dict):
			# 			l = list(methods.NestedDictValues(element))
			# 			s = ', '.join(l)
			# 			manifest[key].append(s)
			# 		else:
			# 			manifest[key].append(element)
			# 	manifest[key] = '\n'.join(manifest[key])
			else:
				manifest[key] = str(value)
		if manifest['metapath'] == 'Corpus':
			nodetype = 'collection'
		elif manifest['name'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
			nodetype = manifest['name'].lower()
		else:
			nodetype = 'branch'
		with open("app/templates/corpus/template_config.yml", 'r') as stream:
			templates = yaml.load(stream)
	except:
		nodetype = None
		templates = yaml.load('')
		errors.append('Unknown Error: The manifest does not exist or could not be loaded.')
	return render_template('corpus/display.html', scripts=scripts,
		breadcrumbs=breadcrumbs, manifest=manifest, errors=errors,
		nodetype=nodetype, templates=templates)


@corpus.route('/update-manifest', methods=['GET', 'POST'])
def update_manifest():
	""" Ajax route for updating manifests."""
	errors = []
	data = request.json
	# data['namespace'] = 'we1sv2.0'
	# Set name and path by branch
	if data['metapath'] == 'Corpus':
		data['nodetype'] = 'collection'
	elif data['name'] in ['RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results']:
		data['nodetype'] = data['name']
		data['metapath'] = 'Corpus,' + data['metapath']
	else:
		data['nodetype'] = 'branch'
		data['metapath'] = 'Corpus,' + data['metapath']
	data['metapath'] =  data['metapath'].replace('Corpus,Corpus,', 'Corpus,').strip(',')
	# Remove empty values
	manifest = {}
	for key, value in data.items():
		if value != '':
			manifest[key] = value
	# Handle dates
	# if 'date' in manifest.keys():
	# 	ls = manifest['date'].splitlines()
	# 	dates = [x.strip() for x in ls]
	# 	new_dates, error_list = methods.check_date_format(dates)
	# 	errors = errors + error_list
	# 	manifest['date'] = new_dates
	if 'created' in manifest.keys():
		created = methods.flatten_datelist(methods.textarea2datelist(manifest['created']))
		if isinstance(created, list) and len(created) == 1:
			created = created[0]
		manifest['created'] = created

	if 'updated' in manifest.keys():
		updated = methods.flatten_datelist(methods.textarea2datelist(manifest['updated']))
		if isinstance(updated, list) and len(updated) == 1:
			updated = updated[0]
		manifest['updated'] = created

	# Handle other textarea strings
	list_props = ['sources', 'contributors', 'queryterms', 'processes', 'notes', 'keywords', 'licenses']
	prop_keys = {
		'sources': { 'main_key': 'title', 'valid_props': ['title', 'path', 'email'] },
		'contributors': { 'main_key': 'title', 'valid_props': ['title', 'email', 'path', 'role', 'group', 'organization'] },
		'licenses': { 'main_key': 'name', 'valid_props': ['name', 'path', 'title'] },
		'queryterms': { 'main_key': '', 'valid_props': [] },
		'processes': { 'main_key': '', 'valid_props': [] },
		'notes': { 'main_key': '', 'valid_props': [] },
		'keywords': { 'main_key': '', 'valid_props': [] }
	}
	for item in list_props:
		if item in manifest and manifest[item] != '':
			all_lines = methods.textarea2dict(item, manifest[item], prop_keys[item]['main_key'], prop_keys[item]['valid_props'])
			if all_lines[item] != []:
				manifest[item] = all_lines[item]

	# list_props = ['publications', 'collectors', 'queryterms', 'processes', 'notes']
	# for item in list_props:
	# 	if item in manifest:
	# 		ls = manifest[item].splitlines()
	# 		manifest[item] = [x.strip() for x in ls]
	nodetype = manifest.pop('nodetype', None)
	if 'OCR' in manifest.keys() and manifest['OCR'] == "on":
		manifest['OCR'] = True

	# Validate the resulting manifest
	if methods.validate_manifest(manifest, nodetype) == True:
		database_errors = methods.update_record(manifest)
		errors = errors + database_errors
	else:
		msg = '''A valid manifest could not be created with the 
		data supplied. Please check your entries against the 
		<a href="/schema" target="_blank">manifest schema</a>.''' 
		errors.append(msg)

	manifest = json.dumps(manifest, indent=2, sort_keys=False)
	if len(errors) > 0:
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
	""" Ajax route to process user export options and write 
	the export files to the temp folder.
	"""
	data = request.json
	# The user only wants to print the manifest
	if data['exportoptions'] == ['manifestonly']:
		query = {'name': data['name'], 'metapath': data['metapath']}
		try:
			result = corpus_db.find_one(query)
			assert result != None
			manifest = {}
			for key, value in result.items():
				if value != '' and value != []:
					manifest[key] = value
			manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
			filename = data['name'] + '.json'
			doc = filename
			methods.make_dir('app/temp')
			filepath = os.path.join('app/temp', filename)
			with open(filepath, 'w') as f:
				f.write(manifest)
		except:
			print('Could not find the manifest in the database.')
	# The user wants a zip of multiple data documents
	else:
		# Get the exportoptions with the correct case
		methods.make_dir('app/temp/Corpus')
		name = data['name']
		metapath = data['metapath']
		# Ensures that there is a Corpus and collection folder with a collection manifest
		methods.make_dir('app/temp/Corpus')
		if metapath == 'Corpus':
			collection = name
		else:
			collection = metapath.split(',')[2]
		methods.make_dir('app/temp/Corpus/' + collection)
		# result = corpus_db.find_one({'metapath': metapath, 'name': collection})
		result = corpus_db.find_one({'metapath': metapath})
		# assert result != None
		manifest = {}
		for key, value in result.items():
			if value != '' and value != []:
				manifest[key] = value
		manifest = json.dumps(manifest, indent=2, sort_keys=False, default=JSON_UTIL)
		filename = name + '.json'
		filepath = os.path.join('app/temp/Corpus', filename)
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
		result = corpus_db.find(
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
				methods.make_dir('app/temp' + folder_path)
				folder = 'app/temp' + path
				doc = item['name'] + '.json'
			# Handle data and branches
			else:
				# If the document has content, just give it a filename
				try:
					assert item['content']
					doc = item['name'] + '.json'
					folder = 'app/temp' + path
					methods.make_dir(folder)
				# Otherwise, use it to create a folder with a manifest file
				except:
					path = os.path.join(path, item['name'])
					folder = 'app/temp' + path
					methods.make_dir(folder)
					doc = item['name'] + '.json'
			filepath = os.path.join(folder, doc)
			output = json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL)
			with open(filepath, 'w') as f:
				f.write(output)
		# Zip up the file structure
		try:
			source_dir = 'app/temp/Corpus'
			doc = 'Corpus.zip'
			methods.zipfolder(source_dir, source_dir)
		except:
			print('Could not make zip archive.')
	return json.dumps({'filename': doc})


@corpus.route('/download-export/<filename>', methods=['GET', 'POST'])
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
	# As a precaution, empty the temp folder
	shutil.rmtree('app/temp')
	methods.make_dir('app/temp')
	return response


@corpus.route('/search1', methods=['GET', 'POST'])
def search():
	""" Page for searching Corpus manifests."""
	scripts = ['js/parsley.min.js', 'js/jquery.twbsPagination.min.js', 'js/corpus/corpus.js','js/dateformat-corpus.js', 'js/jquery-ui.js']
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/search', 'label': 'Search Collections'}]
	if request.method == 'GET':
		return render_template('corpus/search.html', scripts=scripts, breadcrumbs=breadcrumbs)
	if request.method == 'POST':
		result, num_pages, errors = methods.search_collections(request.json)
		if result == []:
			errors.append('No records were found matching your search criteria.')
		return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors})


@corpus.route('/search', methods=['GET', 'POST'])
def search2():
	""" Experimental Page for searching Corpus manifests."""
	scripts = ['js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/corpus/corpus.js', 'js/jquery-sortable-min.js', 'js/corpus/search.js', 'js/dateformat-corpus.js', 'js/jquery-ui.js']
	styles = ['css/query-builder.default.css']	
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/search', 'label': 'Search Collections'}]
	if request.method == 'GET':
		return render_template('corpus/search2.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)
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
		result, num_pages, errors = methods.search_corpus(query, limit, paginated, page, show_properties, sorting)
		# Don't show the MongoDB _id unless it is in show_properties
		if '_id' not in request.json['advancedOptions']['show_properties']:
			for k, v in enumerate(result):
				del result[k]['_id']
		if result == []:
			errors.append('No records were found matching your search criteria.')
		return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)

@corpus.route('/export-search', methods=['GET', 'POST'])
def export_search():
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
		result, num_pages, errors = methods.search_corpus(query, limit, paginated, page, show_properties, sorting)
		if len(result) == 0:
			errors.append('No records were found matching your search criteria.')
		# Need to write the results to temp folder
		for item in result:
			filename = item['name'] + '.json'
			filepath = os.path.join('app/temp', filename)
			with open(filepath, 'w') as f:
				f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
		# Need to zip up multiple files
		if len(result) > 1:
			filename = 'search_results.zip'
			methods.zipfolder('app/temp', 'search_results')
		return json.dumps({'filename': filename, 'errors': errors}, default=JSON_UTIL)

@corpus.route('/delete-manifest', methods=['GET', 'POST'])
def delete_manifest():
	""" Ajax route for deleting manifests."""
	errors = []
	name = request.json['name']
	metapath = request.json['metapath']
	msg = methods.delete_collection(name, metapath)
	if msg != 'success':
		errors.append(msg)
	return json.dumps({'errors': errors})

@corpus.route('/import', methods=['GET', 'POST'])
def import_data():
	""" Page for importing manifests."""
	scripts = [
	'js/corpus/dropzone.js',
	'js/parsley.min.js', 
	'js/corpus/corpus.js',
	'js/corpus/upload.js'
	]
	# Start an import session on page load
	token = datetime.now().strftime('%Y%m%d_') + str(randint(0, 99))
	session['IMPORT_DIR'] = os.path.join(TEMP_DIR, token).replace('\\', '/')

	result = get_server_files()

	# Needs better error handling
	if result != 'error':
		server_files = result
	breadcrumbs = [{'link': '/corpus', 'label': 'Corpus'}, {'link': '/corpus/import', 'label': 'Import Collection Data'}]
	return render_template('corpus/import.html', scripts=scripts, 
			breadcrumbs=breadcrumbs, server_files=server_files, session_token=token)

def get_server_files():
	""" Get the files available for import from the server."""
	file_list = os.listdir(IMPORT_SERVER_DIR)
	# file_list = ['myfile1.json', 'myfile2.json', 'myfile3.json', 'myzipfile1.zip']
	return file_list


@corpus.route('/import-server-file', methods=['GET', 'POST'])
def import_server_data():
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
		metapath = metapath  + ',' + branch
	# If the user's selected filename is in the server import directory
	if filename in os.listdir(IMPORT_SERVER_DIR):
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
				if filename in os.listdir(TRASH_DIR):
					filename = datetime.now().strftime('%Y%m%d%H%M%S_') + filename
				destination = os.path.join(TRASH_DIR, filename)
				shutil.move(source, destination)
			except:
				errors.append('<p>The file could not be read or the manifest could not be inserted in the database.</p>')
	else:
		errors.append('The filename could not be found on the server.')
	if len(errors) > 0:
		return json.dumps({'result': 'fail', 'errors': errors})
	else:
		return json.dumps({'result': 'success', 'errors': []})

@corpus.route('/refresh-server-imports', methods=['GET', 'POST'])
def refresh_server_imports():
	file_list = get_server_files()
	return json.dumps({'file_list': file_list})


@corpus.route('/remove-file', methods=['GET', 'POST'])
def remove_file():
	"""Ajax route triggered when a file is deleted from the file
	uploads table. This function removes the file from the imports
	folder but does not remove it from the database.
	"""
	if request.method == 'POST':
		if os.path.isfile(os.path.join(session['IMPORT_DIR'], request.json['filename'])):
			source = os.path.join(session['IMPORT_DIR'], request.json['filename'])
			destination = os.path.join(session['TRASH_DIR'], request.json['filename'])
			os.rename(source, destination)
		return json.dumps({'response': 'success'})

@corpus.route('/remove-all-files', methods=['GET', 'POST'])
def remove_all_files():
	"""Ajax route triggered when all files are deleted from the file
	uploads table. This function deletes the import session folder
	but does not remove any items already added to the database.
	"""
	# If there is a session import folder
	if os.path.isdir(session['IMPORT_DIR']):
		# Move each file to the trash folder (ensuring it is unique)
		for filename in os.listdir(session['IMPORT_DIR']):
			if filename in os.listdir(TRASH_DIR):
				filename = datetime.now().strftime('%Y%m%d%H%M%S_') + filename
			destination = os.path.join(TRASH_DIR, filename)
			shutil.move(source, destination)
		# Delete the session import folder
		shutil.rmtree(session['IMPORT_DIR'])
		return json.dumps({'response': 'success'})
	else:
		return json.dumps({'response': 'session is empty'})

@corpus.route('/save-upload', methods=['GET', 'POST'])
def save_upload():
	""" Ajax route to create a manifest for each uploaded file  
	and insert it in the database.
	"""
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

		if len(errors) == 0:
			# Set the name and path for the new manifest
			node_metadata = {}
			if request.json['branch'] != '':
				node_metadata['name'] = request.json['branch']
				node_metadata['metapath'] = collection + ',' + request.json['category']
			else:
				node_metadata['name'] = request.json['category']
				node_metadata['metapath'] = collection

		# If the specified metapath does not exist, create it
		if len(errors) == 0:
			parent = list(corpus_db.find({'name': node_metadata['name'], 'metapath': node_metadata['metapath']}))
			if len(parent) == 0:
				try:
					corpus_db.insert_one(node_metadata)
				except:
					errors.append('<p>The specified metapath does not exist and could not be created.</p>')

		# Now create a data manifest for each file and insert it
		if len(errors) == 0:
			for filename in os.listdir(session['IMPORT_DIR']):
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
						result = methods.create_record(manifest)
						print('Is this my error')
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

		if len(errors) == 0:
			return json.dumps({'result': 'success', 'session_token': 'token'})
		else:
			return json.dumps({'errors': errors})

@corpus.route('/upload/', methods=['GET', 'POST'])
def upload():
	"""Ajax route saves each file uploaded by the import function
	to the uploads folder.
	"""
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
					for file in os.listdir(sourcepath):
						if file.endswith('.json'):
							shutil.move(os.path.join(sourcepath, file), os.path.join(session['IMPORT_DIR'], file))
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
	""" Going to this page will quickly empty the database
	of all records along the designated metapath. Use the
	metapath 'all' for delete all records in the database.
	Disable this for production.
	"""
	try:
		if metapath == 'all':
			corpus_db.delete_many({})
			response = 'All records in Corpus database were deleted.'
		else:
			metapath = re.compile('^' + metapath)
			corpus_db.delete_many({'metapath':{'$regex': metapath}})
			response = 'Delete all records under ' + metapath + '.'
	except:
		response = 'There was an error. No records were deleted.'
	return response
