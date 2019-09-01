"""Sources methods.py."""

# import: standard
from datetime import datetime
import itertools
import json
import os
import re
import zipfile
# import: third-party
import dateutil.parser
from flask import current_app
from jsonschema import validate, FormatChecker
import requests
from tableschema_pandas import Storage
from tabulator import Stream
from pymongo import MongoClient
from bson.objectid import ObjectId

# import: app


# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
sources_db = db.Sources
# client = MongoClient('mongodb://mongo:27017')
# DB has one collection, so treat it as the whole DB
# sources_db = client.Sources.Sources

# ----------------------------------------------------------------------------#
# General Helper Functions
# ----------------------------------------------------------------------------#


def allowed_file(filename):
    """Test whether a filename contains an allowed extension.

    Returns a Boolean.
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


def check_date_format(dates):
    """Ensure that a date is correctly formatted and that start dates precede end dates.

    Takes a list of dates and returns a list of dates
    and a list of errors.
    """
    errors = []
    log = []
    for item in dates:
        if ',' in item:
            date_range = item.replace(' ', '').split(',')
            try:
                assert date_range[1] > date_range[0]
                log = log + date_range
            except:
                msg = 'Your end date <code>' + date_range[1] + '</code> must be after your start date <code>' + date_range[0] + '</code>.'
                errors.append(msg)
        else:
            log.append(item)
    for item in log:
        if len(item) > 10:
            date_format = '%Y-%m-%dT%H:%M:%S'
        else:
            date_format = '%Y-%m-%d'
        try:
            item != datetime.strptime(item, date_format).strftime(date_format)
        except:
            msg = 'The date value <code>' + item + '</code> is in an incorrect format. Use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:MM:SS</code>.'
            errors.append(msg)
    new_dates = process_dates(dates)
    return new_dates, errors


def get_page(pages, page):
    """Take a list of paginated results from `paginate()` and returns a single page from the list."""
    try:
        return pages[page - 1]
    except:
        print('The requested page does not exist.')


def make_dir(folder):
    """Check for the existence of directory at the specified file path.

    Creates the directory if it does not exist.
    """
    folder = folder.replace('\\', '/')
    if not os.path.exists(folder):
        os.makedirs(folder)


def NestedDictValues(d):
    """Yield all values in a multilevel dict.

    Returns a generator from which can be cast as a list.
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


def process_dates(dates):
    """Transform a string from an HTML textarea into a schema-valid array."""
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
    """Convert the user input from the search form to a dict.

    Takes strings for the query and show properties fields.
    Returns dicts of keywords and values for both.
    """
    print('temp_query')
    print(temp_query)
    print('temp_show_properties')
    print(temp_show_properties)
    query_props = {}
    for prop in temp_query:
        for key, val in prop.items():
            key = key.strip().strip('"').strip("'")
            val = val.strip().strip('"').strip("'")
            query_props[key] = val
    # for item in temp_query.split('\n'):
    #     prop, val = item.split(':')
    #     prop = prop.strip().strip('"').strip("'")
    #     val = val.strip().strip('"').strip("'")
    #     query_props[prop] = val
    # Convert the properties to show to a list
    show_props = temp_show_properties.split('\n')
    # if show_props == ['']:
    if show_props == []:
        show_props = None
    return query_props, show_props


def validate_manifest(manifest):
    """Validate a manifest against the WE1S schema on GitHub.

    Takes a manifest dict and returns a Boolean.
    """
    schema_file = 'https://github.com/whatevery1says/manifest/raw/master/schema/v2.0/Sources/Sources.json'
    schema = json.loads(requests.get(schema_file).text)
    try:
        validate(manifest, schema, format_checker=FormatChecker())
        return True
    except:
        return False


def zipfolder(source_dir, output_filename):
    """Create a zip archive of a source directory.

    Takes file paths for both the source directory
    and the output file.

    Note that the output filename should not have the
    .zip extension; it is added here.
    """
    # Output filename should be passed to this function without the .zip extension
    zipobj = zipfile.ZipFile(output_filename + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(source_dir) + 1
    for base, _, files in os.walk(source_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


# ----------------------------------------------------------------------------#
# Database Functions
# ----------------------------------------------------------------------------#


def create_record(manifest):
    """Create a new manifest record in the database.

    Takes a manifest dict and returns a list of errors if any.
    """
    errors = []
    if validate_manifest(manifest) is True:
        try:
            assert manifest['name'] not in sources_db.distinct('name')
            sources_db.insert_one(manifest)
        except:
            msg = 'The <code>name</code> <strong>' + manifest['name'] + '</strong> already exists in the database.'
            errors.append(msg)
    else:
        errors.append('Unknown Error: Could not produce a valid manifest.')
    return errors


def delete_source(name, metapath):
    """Delete a source manifest based on name.

    Returns 'success' or an error message string.
    """
    result = sources_db.delete_one({'name': name, 'metapath': metapath})
    if result.deleted_count != 0:
        response = 'success'
    else:
        response = 'Unknown error: The document could not be deleted.'
    return response


def import_manifests(source_files):
    """Loop through the source files and stream them into a dataframe.

    The dataframe is converted to a list of manifest dicts.
    """
    # Set up the storage functions for pandas dataframes
    storage = Storage()
    storage.create('data', {
        'primaryKey': 'name',
        'fields': [
            {'name': 'name', 'type': 'string'},
            {'name': 'metapath', 'type': 'string'},
            {'name': 'namespace', 'type': 'string'},
            {'name': 'title', 'type': 'string'},
            {'name': 'id', 'type': 'string'},
            {'name': '_id', 'type': 'string'},
            {'name': 'description', 'type': 'string'},
            {'name': 'version', 'type': 'string'},
            {'name': 'shortTitle', 'type': 'string'},
            {'name': 'label', 'type': 'string'},
            {'name': 'notes', 'type': 'string'},
            {'name': 'keywords', 'type': 'string'},
            {'name': 'image', 'type': 'string'},
            {'name': 'publisher', 'type': 'string'},
            {'name': 'webpage', 'type': 'string'},
            {'name': 'authors', 'type': 'string'},
            {'name': 'date', 'type': 'string'},
            {'name': 'edition', 'type': 'string'},
            {'name': 'contentType', 'type': 'string'},
            {'name': 'country', 'type': 'string'},
            {'name': 'language', 'type': 'string'},
            {'name': 'citation', 'type': 'string'}
        ]
    })
    path = os.path.join('app', current_app.config['UPLOAD_FOLDER'])
    error_list = []
    print('source_files')
    print(source_files)
    for item in source_files:
        if item.endswith('.xlsx') or item.endswith('.xls'):
            options = {'format': 'xlsx', 'sheet': 1, 'headers': 1}
        else:
            options = {'headers': 1}
        filepath = os.path.join(path, item)
        with Stream(filepath, **options) as stream:
            try:
                stream.headers == ['name', 'metapath', 'namespace', 'title',
                                   'id', '_id', 'description', 'version',
                                   'shortTitle', 'label', 'notes', 'keywords',
                                   'image', 'publisher', 'webpage', 'authors',
                                   'date', 'edition', 'contentType', 'country',
                                   'language', 'citation']
            except:
                col_order = 'name, metapath, namespace, title, id, _id, description, version, shortTitle, label, notes, keywords, image, publisher, webpage, authors, date, edition, contentType, country, language, citation'
                error_list.append('Error: The table headings in ' + item + ' do not match the Sources schema. Please use the headings ' + col_order + ' in that order.')
        with Stream(filepath, **options) as stream:
            try:
                storage.write('data', stream)
            except:
                error_list.append('Error: Could not stream tabular data.')
    os.remove(filepath)
    manifests = []
    properties = {}
    data_dict = storage['data'].to_dict('index')
    print(data_dict)
    for key, values in data_dict.items():
        properties = {k: v for k, v in values.items() if v is not None}
        properties = {k: v.replace('\\n', '\n') for k, v in properties.items()}
        properties['name'] = key
        properties['namespace'] = 'we1sv2.0'
        properties['metapath'] = 'Sources'
        if validate_manifest(properties) is True:
            manifests.append(properties)
        else:
            error_list.append('Could not produce a valid manifest for <code>' + key + '</code>.')
    # Now we're ready to insert into the database
    print(manifests)
    for manifest in manifests:
        db_errors = create_record(manifest)
        error_list = error_list + db_errors
    return manifests, error_list


def search_sources(options):
    """Query the database from the search form.

    Takes a list of values from the form and returns the search results.
    """
    page_size = 10
    errors = []
    if list(sources_db.find()):
        query_properties = options['query']
        show_properties = options['show_properties']
        # query_properties, show_properties = reshape_query_props(options['query'], options['show_properties'])
        if 'regex' in options and options['regex'] is True:
            query = {}
            for k, v in query_properties.items():
                REGEX = re.compile(v)
                query[k] = {'$regex': REGEX}
        else:
            query = query_properties
        result = list(sources_db.find(
            query,
            limit=int(options['limit']),
            projection=show_properties))
        pages = list(paginate(result, page_size=page_size))
        num_pages = len(pages)
        page = get_page(pages, int(options['page']))
        return result, page, num_pages, errors
    errors.append('The Sources database is empty.')
    return [], 1, errors

def idlimit(page_size, query, limit, show_properties, id_range=None):
    """Return page_size number of docs after last_id and new last_id."""
    if id_range is not None:
        start = id_range[0]
        end = id_range[1]
        if start is None and end is not None:
            query['$and'].append({'_id': {'$lte': ObjectId(end)}})
        if start is not None and end is None:
            query['$and'].append({'_id': {'$gte': ObjectId(start)}})
        if start is not None and end is not None:
            query['$and'].append({'_id': {'$gte': ObjectId(start), '$lte': ObjectId(end)}})
        # projection = {item: 1 for item in show_properties}
    cursor = sources_db.find(
        query,
        limit=limit,
        projection=show_properties).limit(page_size)

    # Get the data      
    data = [x for x in cursor]

    if not data:
        # No documents left
        # return None, None
        return None

    # Since documents are naturally ordered with _id,
    # last document will have max id.
    # last_id = data[-1]['_id']

    # Return data and last_id
    return data


def search_sources2(options):
    """Query the database from the search form.

    Takes a list of values from the form and returns the search results.
    """
    errors = []
    if list(sources_db.find()):
        query_properties = options['query']
        show_properties = options['show_properties']
        limit = int(options['limit'])
        # page = options['page']
        page_size = options['page_size']
        id_range = options['id_range']
        # query_properties, show_properties = reshape_query_props(options['query'], options['show_properties'])
        if 'regex' in options and options['regex'] is True:
            query = {}
            for k, v in query_properties.items():
                REGEX = re.compile(v)
                query[k] = {'$regex': REGEX}
        else:
            query = query_properties
        records = idlimit(
            page_size,
            query,
            limit,
            show_properties,
            id_range
        )
        return records, errors


def update_record(manifest):
    """Update a manifest record in the database.

    Takes a manifest dict and returns a list of errors if any.
    """
    errors = []
    if validate_manifest(manifest) is True:
        name = manifest.pop('name')
        metapath = manifest['metapath']
        if '_id' in manifest:
            _id = manifest.pop('_id')
        try:
            sources_db.update_one({'name': name, 'metapath': metapath}, {'$set': manifest}, upsert=False)
        except:
            msg = 'Unknown Error: The record for <code>name</code> <strong>' + name + '</strong> could not be updated.'
            errors.append(msg)
    else:
        errors.append('Unknown Error: Could not produce a valid manifest.')
    return errors


# ----------------------------------------------------------------------------#
# Currently Unused Functions
# ----------------------------------------------------------------------------#


def textarea2dict(fieldname, textarea, main_key, valid_props):
    """Convert a textarea string to a dict containing a list of properties for each line.

    Multiple properties should be formatted as key: value pairs. The key must be separated
    from the value by a space. If ": " occurs in the value, the entire value can be put
    in quotes. Where there is only one value, the key can be omitted, and it will be
    supplied from main_key. A list of valid properties is supplied in valid_props.
    If any property is invalid the function returns a dict with only the error key and
    a list of errors.
    """
    import yaml
    lines = textarea.split('\n')
    all_lines = []
    errors = []

    for line in lines:
        opts = {}
        pattern = ', (' + '[a-z]+: ' + ')'  # Assumes no camel case in the property name
        # There are no options, and the main_key is present
        main = main_key + '|[\'\"]' + main_key + '[\'\"]'
        if re.search('^' + main + ': .+$', line):
            opts[main_key] = re.sub('^' + main + ': ', '', line.strip())
        # There are no options, and the main_key is omitted
        elif re.search(pattern, line) is None:
            opts[main_key] = line.strip()
        # Parse the options
        else:
            line = re.sub(pattern, '\n\\1', line)  # Could be improved to handle more variations
            opts = yaml.load(line.strip())
            for k, _ in opts.items():
                if k not in valid_props:
                    errors.append('The ' + fieldname + ' field is incorrectly formatted or ' + k + ' is not a valid property for the field.')
        all_lines.append(opts)
    if errors == []:
        d = {fieldname: all_lines}
    else:
        d = {'errors': errors}
    return d


def testformat(s):
    """Parse a date and returns a dict.

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
            s = d.strftime("%Y-%m-%dT%H:%M:%SZ")
            dateformat = 'datetime'
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

    Removes 'text' and 'format' properties and replaces their
    container dicts with a simple date string.
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


def list_sources(page_size=10, page=1):
    """Print a list of all sources."""
    if list(sources_db.find()):
        result = list(sources_db.find())
        pages = list(paginate(result, page_size=page_size))
        page = get_page(pages, page)
    else:
        print('The Sources database is empty.')
