"""project.py.

Slightly modified from the version in the GitHub repo in order
to sync better with the WMS.
"""

# pylint: disable=R0201
# pylint: disable=len-as-condition
# pylint: disable=too-many-public-methods

import glob
import hashlib
import json
import re
import os
import sys
import zipfile
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from shutil import copytree, ignore_patterns, rmtree
import nbformat
from bson import Binary, json_util, ObjectId
from pymongo import errors as mongoerrors
from pymongo import ReturnDocument

# For the Workspace, configure the MongoDB client and databases
# Uncomment if using in the Workspace
# def init_db(client, database):
#     from pymongo import MongoClient
#     client = MongoClient(client)
#     db = client['database']
#     return db.Projects, db.Corpus
# db_projects, db_corpus = init_db(client, database)

# Constants
JSON_UTIL = json_util.default

class Project():
    """Model a project.

    Parameters:
    - manifest: dict containing form data for the project manifest.
    - templates_dir: the path to the templates
    - workspace_dir: the path where the project folder is to be saved
    - temp_dir: the path for storing temporary files

    Returns a JSON object with the format `{'response': 'success|fail', 'errors': []}`.

    """

    def __init__(self, manifest, templates_dir, workspace_dir, temp_dir):
        """Initialize the object."""
        self.manifest = manifest
        self.templates_dir = templates_dir
        self.workspace_dir = workspace_dir
        self.temp_dir = temp_dir
        self.reduced_manifest = self.clean(manifest)
        if '_id' in self.reduced_manifest:
            self._id = self.reduced_manifest['_id']
        else:
            self._id = None

    def clean(self, manifest):
        """Get a reduced version of the manifest, removing empty values."""
        data = {}
        for key, val in manifest.items():
            if val not in ['', [], ['']] and not key.startswith('builder_'):
                data[key] = val
        return data

    def clean_nb(self, nbfile, clean_outputs=True,
                 clean_notebook_metadata_fields=None,
                 clean_cell_metadata_fields=None,
                 clean_tags=None,
                 clean_empty_cells=False,
                 save=False):
        """Clean metadata fields and outputs from notebook.

        Cleans outputs only by default. Takes a path to the notebook file.
        Returns a json object with the cleaned notebook. Based on nbtoolbelt:
        https://gitlab.tue.nl/jupyter-projects/nbtoolbelt/blob/master/src/nbtoolbelt/cleaning.py
        """
        # Read the file
        try:
            nb = nbformat.read(nbfile, as_version=4)
        except RuntimeError as err:
            print('{}: {}'.format(type(err).__name__, err), sys.stderr)
        freq = defaultdict(int)  # number of cleanings
        # delete notebook (global) metadata fields
        if isinstance(clean_notebook_metadata_fields, list) \
            and len(clean_notebook_metadata_fields) > 0:
            for field in clean_notebook_metadata_fields:
                if field in nb.metadata:
                    del nb.metadata[field]
                    freq['global ' + field] += 1
        # delete empty cells, if desired
        num = len(nb.cells)
        if clean_empty_cells:
            nb.cells = [cell for cell in nb.cells if self.count_source(cell.source)[0]]
        if num > len(nb.cells):
            freq['empty cells'] = num - len(nb.cells)
        # traverse all cells, and delete fields
        for _, cell in enumerate(nb.cells):  # Assign an index if needed for debugging
            count = cell.cell_type
            # delete cell metadata fields
            if isinstance(clean_cell_metadata_fields, list) and len(clean_cell_metadata_fields) > 0:
                for field in clean_cell_metadata_fields:
                    if field in cell.metadata:
                        del cell.metadata[field]
                        freq['cell ' + field] += 1
            # delete cell tags
            if 'tags' in cell.metadata and isinstance(clean_tags, list) and len(clean_tags) > 0:
                removed_tags = {tag for tag in cell.metadata.tags if tag in clean_tags}
                for tag in removed_tags:
                    freq['tag ' + tag] += 1
                clean_tags = [tag for tag in cell.metadata.tags if tag not in clean_tags]
                if clean_tags:
                    cell.metadata.tags = clean_tags
                else:
                    del cell.metadata['tags']
            # clean outputs of code cells, if requested
            if count == 'code' and clean_outputs:
                if cell.outputs:
                    cell.outputs = []
                    freq['outputs'] += 1
                cell.execution_count = None
        # re-write the json file or return it to a variable
        if save:
            with open(nbfile, 'w') as fn:
                fn.write(json.dumps(nb, indent=2))
        else:
            return json.dumps(nb, indent=2)

    def compare_files(self, existing_file, new_file):
        """Hash and compare two files.

        Returns True if they are equivalent.
        """
        existing_hash = hashlib.sha256(open(existing_file, 'rb').read()).digest()
        new_hash = hashlib.sha256(open(new_file, 'rb').read()).digest()
        return existing_hash == new_hash

    def copy(self, name, version=None):
        """Insert a copy of the current project into the database using a new name and _id.

        If no version is supplied, the latest version is used. Regardless, the new project
        is reset to version 1.
        """
        # Delete the _id and rename the project
        del self.reduced_manifest['_id']
        self.reduced_manifest['name'] = name
        # Get the latest version number if none is supplied
        if version is None:
            version = self.get_latest_version_number()
        # Get the version dict and reset the version number and date
        version_dict = self.get_version(version)
        version_dict['version_number'] = 1
        now = datetime.today().strftime('%Y%m%d%H%M%S')
        version_dict['version_date'] = now
        version_dict['version_name'] = now + '_v1_' + self.reduced_manifest['name']
        self.reduced_manifest['content'] = [version_dict]
        # Save the manifest
        try:
            projects_db.insert_one(self.reduced_manifest) # pylint: disable=undefined-variable
            return json.dumps(
                {'result': 'success',
                 'project_dir': version_dict['version_name'],
                 'errors': []
                })
        except mongoerrors.OperationFailure as err:
            print(err.code)
            print(err.details)
            return json.dumps(
                {'result': 'fail',
                 'errors': ['Unknown error: Could not insert the new project from the database.']
                })

    def copy_templates(self, templates, project_dir):
        """Copy the workflow templates from the templates folder to the a project folder."""
        try:
            copytree(templates,
                     project_dir,
                     ignore=ignore_patterns('.ipynb_checkpoints', '__pycache__')
                    )
            return []
        except IOError:
            return '<p>Error: The templates could not be copied to the project directory.</p>'

    def count_source(self, source):
        """Count number of non-blank lines, words, and non-whitespace characters.

        Used by clean_nb().

        :param source: string to count
        :return: number of non-blank lines, words, and non-whitespace characters
        """
        lines = [line for line in source.split('\n') if line and not line.isspace()]
        words = source.split()
        chars = ''.join(words)
        return len(lines), len(words), len(chars)

    def create_version_dict(self, path=None, version=None):
        """Create and return a version dict.

        If a project path is given, the project folder is zipped
        and compared to the latest existing zip archive. If it
        differs, a new dict is created with a higher version number.
        """
        # Get the latest version number or 1 if it doesn't exist
        if version is None:
            version = self.get_latest_version_number()
        version_dict = self.get_version(version)
        # Create an empty dict of the manifest doesn't have one
        if version_dict == 0 or version_dict is None:
            version_dict = {}
        # If a path is given, zip it and compare to the existing hash
        if path is not None:
            now = datetime.today().strftime('%Y%m%d%H%M%S')
            version_dict['version_name'] = now + '_v' + str(version) + self.reduced_manifest['name']
            version_dict['version_number'] = version

            # Make sure there is a zipfile to compare
            # Zip the project path
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)
            new_zipfile_path = self.temp_dir + '/' + version_dict['version_name'] + '.zip'
            new_zipfile = zipfile.ZipFile(new_zipfile_path, 'w', zipfile.ZIP_DEFLATED)
            rootlen = len(path) + 1
            for base, _, files in os.walk(path):
                # Create local paths and write them to the new zipfile
                for file in files:
                    fn = os.path.join(base, file)
                    new_zipfile.write(fn, fn[rootlen:])
                # Compare the hashes
            if 'zipfile' in version_dict and version_dict['zipfile'] is not None:
                result = self.compare_files(version_dict['zipfile'], new_zipfile)
                # If the zipfiles are not the same iterate the version
                if not result:
                    version = version + 1
                    version_dict['version_number'] = version
            with open(new_zipfile_path, 'rb') as f:
                version_dict['zipfile'] = Binary(f.read())
            # Now remove the temporary zipfile
            new_zipfile.close()
            os.remove(new_zipfile_path)
        return version_dict

    def delete(self, version=None):
        """Delete a project or a project version, if the number is supplied."""
        if version is None:
            try:
                result = projects_db.delete_one({'_id': ObjectId(self._id)}) # pylint: disable=undefined-variable
                if result.deleted_count > 0:
                    return {'result': 'success', 'errors': []}
                return {
                    'result': 'fail',
                    'errors': ['Unknown error: Could not delete the project from the database.']
                    }
            except mongoerrors.OperationFailure as err:
                print(err.code)
                print(err.details)
                return {
                    'result': 'fail',
                    'errors': ['Unknown error: Could not delete the project from the database.']
                    }
        else:
            try:
                for index, item in enumerate(self.reduced_manifest['content']):
                    if item['version_number'] == version:
                        del self.reduced_manifest['content'][index]
                        projects_db.update_one({'_id': ObjectId(self._id)}, # pylint: disable=undefined-variable
                                               {'$set': {
                                                   'content': self.reduced_manifest['content']
                                                   }
                                               },
                                               upsert=False)
            except mongoerrors.OperationFailure as err:
                print(err.code)
                print(err.details)
                return {
                    'result': 'fail',
                    'errors': ['Unknown error: Could not delete the project from the database.']
                    }

    def exists(self):
        """Test whether the project already exists in the database."""
        test = projects_db.find_one({'_id': ObjectId(self._id)}) # pylint: disable=undefined-variable
        if test is not None:
            return True
        return False

    def export(self, version=None):
        """Export a project in the Workspace."""
        errors = []
        # Get the version dict. Use the latest version if no version number is supplied.
        if version is None:
            version_dict = self.get_latest_version()
        else:
            version_dict = self.get_version(version)
        # Set the filename and path to write to
        zipname = version_dict['version_name'] + '.zip'
        exports_dir = os.path.join(self.workspace_dir, 'exports')
        # 1. First try to get the zip file from the manifest and copy it to the exports folder
        if 'version_zipfile' in version_dict:
            try:
                zip_file = version_dict['version_zipfile']
                with open(os.path.join(exports_dir, zipname), 'wb') as f:
                    f.write(zip_file)
            except IOError:
                errors.append('Error: Could not write the zip archive to the exports directory.')
        # 2. Try to find an active project in the Workspace and zip it to exports
        elif os.path.exists(os.path.join(self.workspace_dir, version_dict['version_name'])):
            try:
                project_dir = os.path.join(self.workspace_dir, version_dict['version_name'])
                zip_file = self.zip(zipname, project_dir, exports_dir)
            except RuntimeError:
                msg = 'Error: Could not zip project folder from the Workspace to the exports directory.'
                errors.append(msg)
        # 3. Create a new project in the exports directory and populate from the database
        else:
            # Make a version folder in the exports directory
            project_dir = exports_dir + '/' + version_dict['version_name']
            os.makedirs(project_dir, exist_ok=True)
            # Get the data and put a manifest in it and write data to the caches/json folder
            result = corpus_db.find(self.reduced_manifest['db_query']) # pylint: disable=undefined-variable
            try:
                with open(os.path.join(project_dir, 'datapackage.json'), 'w') as f:
                    f.write(json.dumps(
                        self.reduced_manifest,
                        indent=2,
                        sort_keys=False,
                        default=JSON_UTIL
                        ))
                json_caches = os.path.join(project_dir, 'project_data/json')
                os.makedirs(json_caches, exist_ok=True)
                for item in result:
                    filename = os.path.join(json_caches, item['name'] + '.json')
                    with open(filename, 'w') as f:
                        f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
            except IOError:
                errors.append('<p>Error: Could not write data files to the caches directory.</p>')
            # Zip up the project folder, then delete the folder
            zip_file = self.zip(zipname, project_dir, exports_dir)
            rmtree(project_dir)
        # Return the path to the zip archive
        if len(errors) > 0:
            return json.dumps({'result': 'fail', 'errors': errors})
        return json.dumps(
            {'result': 'success',
                'filename': zipname,
                'errors': errors
            })

    def get_latest_version_number(self):
        """Get the latest version number from the versions dict.

        Returns an integer or 1, if no version information is available.
        """
        version_numbers = []
        if 'content' in self.reduced_manifest and len(self.reduced_manifest['content']) > 0:
            for version in self.reduced_manifest['content']:
                version_numbers.append(int(version['version_number']))
            _latest_version_number = max(version_numbers)
        else:
            _latest_version_number = 1
        return _latest_version_number

    def get_latest_version(self):
        """Get the dict for the latest version."""
        _latest_version = {}
        version_numbers = []
        if 'content' in self.reduced_manifest and len(self.reduced_manifest['content']) > 0:
            for version in self.reduced_manifest['content']:
                version_numbers.append(int(version['version_number']))
            _latest_version_number = max(version_numbers)
            for version in self.reduced_manifest['content']:
                if version['version_number'] == _latest_version_number:
                    _latest_version = version['version_number']
        return self.get_version(_latest_version)


    def get_version(self, value, key='number'):
        """Get the dict for a specific version.

        Accepts an integer version number by default. If the key is 'number',
        'name', or 'date', that value is used to find the dict.
        """
        if 'content' in self.reduced_manifest:
            versions = self.reduced_manifest['content']
            for version in versions:
                if version['version_' + str(key)] == str(value):
                    return version
        else:
            # Return 0 to tell create_version_dict() to start with {}
            # raise ValueError('No versions were included in the manifest.')
            return 0

    def launch(self, workflow, version=None, new=True):
        """Prepare the project in the Workspace.

        - If the user does not have any versions stored in the
          database, a new v1 project_dir is created.
        - Otherwise, if the user clicks the main rocket icon, a new
          project_dir is created based on the latest version.
        - If the user clicks on a specific version's rocket icon,
          a project_dir based on that version's datapackage is created.
        - Where possible, a version is unzipped to the Workspace.
        - Otherwise, the data is written to the project_dir from the
          database.
        """
        # If the manifest has a zipfile, skip Option 1
        if 'content' in self.reduced_manifest:
            for item in self.reduced_manifest['content']:
                if 'zipfile' in item:
                    version = 'latest'

        # Get a timestamp
        now = datetime.today().strftime('%Y%m%d%H%M%S')

        # Option 1. Generate a project_dir for a new v1
        if new and version is None:
            version_name = now + '_v1_' + self.reduced_manifest['name']
            self.reduced_manifest['content'] = {
                'version_date': now,
                'version_number': 1,
                'version_name': version_name,
                'version_workflow': workflow
            }
            project_dir = os.path.join(self.workspace_dir, version_name)
            templates = os.path.join(self.templates_dir, workflow)
            errors = self.make_new_project_dir(project_dir, templates)
            if errors == []:
                return json.dumps({'result': 'success', 'project_dir': project_dir, 'errors': []})
            return json.dumps({'result': 'fail', 'errors': errors})

        # Option 2. Generate a new project_dir based on the latest version
        if new and version is not None:
            version_dict = self.get_latest_version()
            next_version_number = version_dict['version_number'] + 1
            next_version_name = now + '_v' + str(next_version_number) + '_' + self.reduced_manifest['name']
            next_version = {
                'version_date': now,
                'version_number': next_version_number,
                'version_workflow': workflow,
                'version_name': next_version_name,
                'version_zipfile': version_dict['version_zipfile']
            }
            self.reduced_manifest['content'] = next_version
            project_dir = os.path.join(self.workspace_dir, next_version_name)
            try:
                self.unzip(version_dict['version_zipfile'], project_dir)
                return json.dumps({'result': 'success', 'project_dir': project_dir, 'errors': []})
            except RuntimeError:
                errors = ['Unknown error: Could not unzip the project datapackage to the project directory.']
                return json.dumps({'result': 'fail', 'errors': errors})

        # Option 3. Launch a specific version
        if not new:
            if version is None:
                version_dict = self.get_latest_version()
            else:
                version_dict = self.get_version(version)
            print('Launching ' + version_dict['version_name'])
            project_dir = os.path.join(self.workspace_dir, version_dict['version_name'])
            # If the project is live in the workspace, return a link to the folder
            if os.path.exists(project_dir):
                return json.dumps({'result': 'success', 'project_dir': project_dir, 'errors': []})
            # Otherwise, unzip the datapackage from the manifest to the workspace
            try:
                self.unzip(version_dict['version_zipfile'], project_dir, binary=True)
                print('Unzipped to ' + project_dir)
            except RuntimeError:
                errors.append('<p>Unknown error: Could not unzip the project datapackage to the project directory.</p>')
                return json.dumps({'result': 'fail', 'errors': errors})

    def make_new_project_dir(self, project_dir, templates):
        """Provide a helper function for Project.launch()."""
        errors = []
        # The project_dir must not already exist
        error = self.copy_templates(templates, project_dir)
        if error != []:
            errors.append(error)
        # If the there is a db_query, get the data
        if 'db_query' in self.reduced_manifest:
            try:
                result = list(corpus_db.find(self.reduced_manifest['db_query'])) # pylint: disable=undefined-variable
                if len(result) == 0:
                    errors.append('<p>The database query returned no results.</p>')
            except mongoerrors.OperationFailure as err:
                print(err.code)
                print(err.details)
                msg = '<p>Unknown Error: The database query could not be executed.</p>'
                errors.append(msg)
            # Write the data manifests to the caches/json folder
            try:
                json_caches = os.path.join(project_dir, 'caches/json')
                os.makedirs(json_caches, exist_ok=True)
                with open(os.path.join(project_dir, 'datapackage.json'), 'w') as f:
                    f.write(json.dumps(
                        self.reduced_manifest,
                        indent=2,
                        sort_keys=False,
                        default=JSON_UTIL
                        ))

                for item in result:
                    filename = os.path.join(json_caches, item['name'] + '.json')
                    with open(filename, 'w') as f:
                        f.write(json.dumps(item, indent=2, sort_keys=False, default=JSON_UTIL))
            except IOError:
                errors.append('<p>Error: Could not write data files to the caches directory.</p>')
        else:
            errors.append('<p>Please enter a database query in the Data Resources tab.</p>')

        return errors

    def parse_version(self, s, output=None):
        """Separate a project folder name into its component parts.

        The output argument allows you to return a single component.
        """
        version = re.search('(.+)_v([0-9]+)_(.+)', s)
        if output == 'date':
            return version.group(1)
        if output == 'number':
            return version.group(2)
        if output == 'name':
            return version.group(3)
        return version.group(1), version.group(2), version.group(3)

    def print_manifest(self):
        """Print the manifest."""
        print(json.dumps(self.reduced_manifest, indent=2, sort_keys=False, default=JSON_UTIL))

    def save(self, path=None):
        """Handle save requests from the WMS or workspace.

        Default behaviour: Insert a new record.
        """
        # Determine if the project exists in the database
        if self.exists() and self._id is not None:
            action = 'update'
        else:
            action = 'insert'
        # If a path is supplied, zip it and create a manifest version
        if path is not None:
            self.reduced_manifest['content'] = self.create_version_dict(path)
        # Execute the database query and return the result
        return self.save_record(action)

    def save_record(self, action='insert'):
        """Insert or update a record in the database.

        This is a helper function to reduce code repetition.
        """
        try:
            if action == 'update':
                result = projects_db.find_one_and_update( # pylint: disable=undefined-variable
                    {'_id': ObjectId(self._id)},
                    {'$set': self.reduced_manifest},
                    upsert=False,
                    projection={'_id': True},
                    return_document=ReturnDocument.AFTER
                    )
                _id = result['_id']
            else:
                result = projects_db.insert_one(self.reduced_manifest) # pylint: disable=undefined-variable
                _id = result.inserted_id
            return {'result': 'success', '_id': _id, 'errors': []}
        except mongoerrors.OperationFailure as err:
            print(err.code)
            print(err.details)
            return {'result': 'fail', 'errors': ['Error: Could not update the database.']}

    def save_as(self, path=None, new_name=None):
        """Handle save as requests from the WMS or workspace.

        Default behaviour: Insert a new record.
        """
        # Determine if a new name is supplied
        if new_name is None:
            return {'result': 'fail', 'errors': ['No name has been supplied for the new project.']}
        # If a path is supplied, zip the folder and create a version 1
        if path is not None:
        # Create a new project folder
            try:
                path_parts = path.split('/')
                path_parts[-1] = datetime.today().strftime('%Y%m%d%H%M%S_') + new_name
                new_path = '/'.join(path_parts)
                copytree(path, new_path)
            except OSError:
                return {
                    'result': 'fail',
                    'errors': ['A project folder with that name already exists. Please try another name.']
                    }
            # Clear Outputs on a glob of all ipynb files
            try:
                for filename in glob.iglob(path + '/**', recursive=True):
                    if filename.endswith('.ipynb'):
                        self.clean_nb(filename, clean_empty_cells=True, save=True)
            except OSError:
                # Delete the new directory and fail since we
                # have no way to provide this as a warning.
                rmtree(new_path)
                return {
                    'result': 'fail',
                    'errors': ['Could not clear the notebook variables in the new project folder.']
                    }
            # Change the manifest name and delete the _id
            self.reduced_manifest['name'] = new_name
            if '_id' in self.reduced_manifest:
                del self.reduced_manifest['_id']
            # If there are any project configs, start files, etc.,
            # they should be reset here.
            # Change the manifest version dict
            # Not sure if this call works; it might have to call 0
            self.reduced_manifest['content'] = self.create_version_dict(path, 1)
            # Now insert the record in the database
            return self.save_record('insert')
        # We just need to insert a new database record with the new name
        self.reduced_manifest['name'] = new_name
        # We probably don't want to delete the version history,
        # but we can't clear notebook outputs whilst the version
        # is zipped. Let's live with this discrepancy for now.
        # self.reduced_manifest['content'] = []
        if '_id' in self.reduced_manifest:
            del self.reduced_manifest['_id']
        return self.save_record('insert')

    def unzip(self, source=None, output_path=None, binary=False):
        """Unzip the specified file to a project folder in the Workspace.

        Uses the current path if one is not specified.
        """
        if binary:
            # Copy the zip archive to memory; then unzip it to the output path
            temp_zipfile = zipfile.ZipFile(BytesIO(source))
            temp_zipfile.extractall(output_path)
            return {'result': 'success', 'output_path': output_path, 'errors': []}
        # Otherwise, the source is a filepath
        try:
            with zipfile.ZipFile(source, 'r') as zip_ref:
                zip_ref.extractall(output_path)
            return {'result': 'success', 'output_path': output_path, 'errors': []}
        except RuntimeError:
            return {'result': 'fail', 'errors': ['Could not unzip the file at ' + source + '.']}


    def zip(self, filename, source_dir, destination_dir):
        """Create a zip archive of the project folder and writes it to the destination folder."""
        errors = []
        try:
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
        except RuntimeError:
            errors.append('The destination directory does not exist, and it could not be created.')
            return {'result': 'fail', 'errors': errors}
        try:
            zip_path = os.path.join(destination_dir, filename)
            zipobj = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
            rootlen = len(source_dir) + 1
            for base, _, files in os.walk(source_dir):
                for file in files:
                    fn = os.path.join(base, file)
                    zipobj.write(fn, fn[rootlen:])
            return {'result': 'success', 'zip_path': zip_path, 'errors': []}
        except RuntimeError:
            errors.append('<p>Unknown error: a zip archive could not be created with the supplied source directory and filename.</p>')
            return {'result': 'fail', 'errors': errors}

# Send feedback to the notebook cell
# print('Project module loaded.')
