"""methods.py"""

import os
import itertools
import json
import re
import requests
import shutil
import zipfile

from datetime import datetime
from jsonschema import validate, FormatChecker

import tabulator
from tabulator import Stream

import pandas as pd
from tableschema_pandas import Storage

import pymongo
from pymongo import MongoClient
from pymongo.collation import Collation

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
corpus_db = db.Corpus

# ----------------------------------------------------------------------------#
# General Helper Functions
# ----------------------------------------------------------------------------#


def allowed_file(filename):
    """Tests whether a filename contains an allowed extension.

    Returns a Boolean.
    """
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


def check_date_format(dates):
    """Ensures that a date is correctly formatted
    and that start dates precede end dates.

    Takes a list of dates and returns a list of dates
    and a list of errors.
    """
    errors = []
    log = []
    for item in dates:
        if ',' in item:
            range = item.replace(' ', '').split(',')
            try:
                assert range[1] > range[0]
                log = log + range
            except:
                msg = 'Your end date <code>' + range[1] + '</code> must be after your start date <code>' + range[0] + '</code>.'
                errors.append(msg)
        else:
            log.append(item)
    for item in log:
        if len(item) > 10:
            format = '%Y-%m-%dT%H:%M:%S'
        else:
            format = '%Y-%m-%d'
        try:
            item != datetime.strptime(item, format).strftime(format)
        except:
            msg = 'The date value <code>' + item + '</code> is in an incorrect format. Use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:MM:SS</code>.'
            errors.append(msg)
    new_dates = process_dates(dates)
    return new_dates, errors


def get_page(pages, page):
    """Takes a list of paginated results form `paginate()` and
    returns a single page from the list.
    """
    try:
        return pages[page-1]
    except:
        print('The requested page does not exist.')


def make_dir(folder):
    """Checks for the existence of directory at the specified file
    path and creates one if it does not exist.
    """
    folder = folder.replace('\\', '/')
    if not os.path.exists(folder):
        os.makedirs(folder)


def NestedDictValues(d):
    """ Yields all values in a multilevel dict. Returns a generator
    from which can be cast as a list.
    """
    for v in d.values():
        if isinstance(v, list):
            yield from NestedDictValues(v[0])
            break
        if isinstance(v, dict):
            yield from NestedDictValues(v)
        else:
            yield v


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


def process_dates(dates):
    """Transforms a string from an HTML textarea into an
    array that validates against the WE1S schema.
    """
    new_dates = []
    d = {}
    # Determine if the dates are a mix of normal and precise dates
    contains_precise = []
    for item in dates:
        if ',' in item:
            start, end = item.replace(' ', '').split(',')
            if len(start) > 10 or len(end) > 10:
                contains_precise.append('precise')
            else:
                contains_precise.append('normal')
        elif len(item) > 10:
            contains_precise.append('precise')
        else:
            contains_precise.append('normal')
    # Handle a mix of normal and precise dates
    if 'normal' in contains_precise and 'precise' in contains_precise:
        d['normal'] = []
        d['precise'] = []
        for item in dates:
            if ',' in item:
                start, end = item.replace(' ', '').split(',')
                if len(start) > 10 or len(end) > 10:
                    d['precise'].append({'start': start, 'end': end})
                else:
                    d['normal'].append({'start': start, 'end': end})
            else:
                if len(item) > 10:
                    d['precise'].append(item)
                else:
                    d['normal'].append(item)
                new_dates.append(d)
    # Handle only precise dates
    elif 'precise' in contains_precise:
        d['precise'] = []
        for item in dates:
            if ',' in item:
                start, end = item.replace(' ', '').split(',')
                d['precise'].append({'start': start, 'end': end})
            else:
                d['precise'].append(item)
        new_dates.append(d)
    # Handle only normal dates
    else:
        for item in dates:
            if ',' in item:
                start, end = item.replace(' ', '').split(',')
                new_dates.append({'start': start, 'end': end})
            else:
                new_dates.append(item)
    return new_dates


def reshape_query_props(temp_query, temp_show_properties):
    """Converts the user input from the search form to
    a dict of properties.

    Takes strings for the query and show properties fields.
    Returns dicts of keywords and values for both.
    """
    query_props = {}
    print("temp_query")
    # {'$and': [{'name': 'gemma'}, {'path': ',Corpus,'}]}
    print(temp_query)
    keys = temp_query.keys()
    key = list(keys)[0]
    for item in temp_query[key]:
        print(item)
    for item in temp_query.split('\n'):
        prop, val = item.split(':')
        prop = prop.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        query_props[prop] = val
    # Convert the properties to show to a list
    show_props = temp_show_properties.split('\n')
    if show_props == ['']:
        show_props = None
    return query_props, show_props


def validate_manifest(manifest, nodetype):
    """Validates a manifest against the WE1S schema on GitHub.

    Takes a manifest dict and a nodetype string (which identifies
    which subschema to validate against). Returns a Boolean.
    """
    url = 'https://raw.githubusercontent.com/whatevery1says/manifest/master/schema/v2.0/Corpus/'
    if nodetype in ['collection', 'RawData', 'ProcessedData', 'Metadata', 'Outputs', 'Results', 'Data']:
        filename = nodetype + '.json'
    else:
        filename = 'PathNode.json'
    schema_file = url + filename
    schema = json.loads(requests.get(schema_file).text)
    print(schema_file)
    print(manifest)
    try:
        validate(manifest, schema, format_checker=FormatChecker())
        return True
    except:
        return False


def zipfolder(source_dir, output_filename):
    """Creates a zip archive of a source directory.

    Takes file paths for both the source directory
    and the output file.

    Note that the output filename should not have the
    .zip extension; it is added here.
    """
    # Output filename should be passed to this function without the .zip extension
    zipobj = zipfile.ZipFile(output_filename + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(source_dir) + 1
    for base, dirs, files in os.walk(source_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


# ----------------------------------------------------------------------------#
# Database Functions
# ----------------------------------------------------------------------------#


def create_record(manifest):
    """ Creates a new manifest record in the database.

    Takes a manifest dict and returns a list of errors if any.
    """
    errors = []
    try:
        result = list(corpus_db.find({'name': manifest['name'], 'metapath': manifest['metapath']}))
        assert result == []
        # assert manifest['name'] not in corpus_db.distinct('name')
        corpus_db.insert_one(manifest)
    except:
        """We need to add some code here that looks for a LexisNexis
        `doc_id` and appends a portion of it to `manifest['name']`
        until it is unique within the collection. Otherwise, add a
        random number or display the error below."""
        msg = 'The <code>name</code> <strong>' + manifest['name'] + '</strong> already exists along the metapath <code>' + manifest['metapath'] + '</code> in the database.'
        errors.append(msg)
    return errors


def delete_collection(name, metapath):
    """Deletes a collection manifest based on name.

    Returns 'success' or an error message string.
    """
    result = corpus_db.delete_one({'name': name, 'metapath': metapath})
    if result.deleted_count != 0:
        return 'success'
    else:
        return 'Unknown error: The document could not be deleted.'


def search_collections(values):
    """Queries the database from the search form.

    Takes a list of values from the form and returns the search results.
    """
    if 'paginated' in values:
        paginated = values['paginated']
    else:
        paginated = True
    page_size = 10
    errors = []
    if len(list(corpus_db.find())) > 0:
        query = values['query']
        if values['regex'] == True:
            query = {}
            for k, v in query_properties.items():
                REGEX = re.compile(v)
                query[k] = {'$regex': REGEX}
        else:
            query = query_properties
        limit = int(values['advancedOptions']['limit']) or 0
        result = list(corpus_db.find(
            query,
            limit=limit,
            projection=show_properties)
        )
        # Double the result for testing
        # result = result + result + result + result + result
        # result = result + result + result + result + result
        if paginated == True:
            pages = list(paginate(result, page_size=page_size))
            num_pages = len(pages)
            page = get_page(pages, int(values['page']))
            return page, num_pages, errors
        else:
            return result, 1, errors
    else:
        errors.append('The Corpus database is empty.')
        return [], 1, errors


def search_corpus(query, limit, paginated, page, show_properties, sorting):
    """Uses the query generated in /search2 and returns the search results.
    """
    page_size = 10
    errors = []
    """
    # Check that the query has a valid path within the Corpus
    # Good for testing
    key = list(query.keys())[0]
    is_path = next((item for item in query.get(key) if item.get('path')), False)
    # False if the query does not have a path; set it to ',Corpus,' by default
    if is_path == False:
        query.get(key).append({'path': ',Corpus,'})
    print(query.get(key))
    is_corpus_path = next((item for item in query.get(key) if item.get('path') != None and item.get('path').startswith(',Corpus,')), False)
    # False if the path is not in the Corpus; return an error
    if is_corpus_path == False:
        errors.append('Please supply a valid path within the Corpus.')
    """
    if len(list(corpus_db.find())) > 0:
        result = corpus_db.find(
            query,
            limit=limit,
            projection=show_properties).collation(Collation(locale='en_US', numericOrdering=True))
        if sorting != []:
            result = result.sort(sorting)
        else:
            result = result.sort('name', pymongo.ASCENDING)
        result = list(result)
        if result != []:
            # Double the result for testing
            # result = result + result + result + result + result
            # result = result + result + result + result + result
            if paginated == True:
                pages = list(paginate(result, page_size=page_size))
                num_pages = len(pages)
                page = get_page(pages, page)
                return page, num_pages, errors
            else:
                return result, 1, errors
        else:
            return [], 1, errors
    else:
        errors.append('The Corpus database is empty.')
        return [], 1, errors


def update_record(manifest):
    """ Updates a manifest record in the database.

    Takes a manifest dict and returns a list of errors if any.
    """
    errors = []
    # Need to set the nodetype
    nodetype = 'collection'
    if validate_manifest(manifest, nodetype) == True:
        name = manifest.pop('name')
        metapath = manifest['metapath']
        _id = manifest.pop('_id')
        try:
            corpus_db.update_one({'name': name, 'metapath': metapath}, {'$set': manifest}, upsert=False)
        except pymongo.errors.PyMongoError as e:
            # print(e.__dict__.keys())
            # print(e._OperationFailure__details)
            msg = 'Unknown Error: The record for <code>name</code> <strong>' + name + '</strong> could not be updated.'
            errors.append(msg)
    else:
        errors.append('Unknown Error: Could not produce a valid manifest.')
    return errors


# ----------------------------------------------------------------------------#
# Currently Unused Functions
# ----------------------------------------------------------------------------#


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
            elif re.search(pattern, line) == None:
                opts[main_key] = line.strip()
            all_lines.append(opts)
    if errors == []:
        d = {fieldname: all_lines}
    else:
        d = {'errors' : errors}
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


def list_collections(page_size=10, page=1):
    """Prints a list of all publications.
    """
    if len(list(corpus_db.find())) > 0:
        result = list(collections.find())
        pages = list(paginate(result, page_size=page_size))
        page = get_page(pages, page)
    else:
        print('The Corpus database is empty.')
