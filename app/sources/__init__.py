"""Sources __init__.py."""

# import: standard
import itertools
import json
import os
import re
import shutil
import yaml
# import: third-party
from bson import BSON
from bson import json_util
from bson.objectid import ObjectId
from flask import Blueprint, make_response, render_template, request, url_for, current_app
from jsonschema import validate, FormatChecker
import pymongo
from pymongo import MongoClient
import requests
import tabulator
from werkzeug.utils import secure_filename
# import: app
from app.sources.helpers import methods  # pylint: disable=cyclic-import
from app import db  # pylint: disable=cyclic-import
sources_db = db.client[db.sources]['Sources']
JSON_UTIL = json_util.default

# Database info should be imported by the code above,
# but the code below is retained in case it needs
# to be activated for testing.

# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
# client = MongoClient('mongodb://localhost:27017')
# db = client.we1s
# sources_db = db.Sources
# client = MongoClient('mongodb://mongo:27017')
# DB has one collection, so treat it as the whole DB
# sources_db = client.Sources.Sources

sources = Blueprint('sources', __name__, template_folder='sources')

# ----------------------------------------------------------------------------#
# Constants.
# ----------------------------------------------------------------------------#


ALLOWED_EXTENSIONS = ['xlsx']
lang_list = ['aar', 'abk', 'ace', 'ach', 'ada', 'ady', 'afa', 'afh', 'afr', 'ain', 'aka', 'akk', 'alb (B)', 'sqi (T)', 'ale', 'alg', 'alt', 'amh', 'ang', 'anp', 'apa', 'ara', 'arc', 'arg', 'arm (B)', 'hye (T)', 'arn', 'arp', 'art', 'arw', 'asm', 'ast', 'ath', 'aus', 'ava', 'ave', 'awa', 'aym', 'aze', 'bad', 'bai', 'bak', 'bal', 'bam', 'ban', 'baq (B)', 'eus (T)', 'bas', 'bat', 'bej', 'bel', 'bem', 'ben', 'ber', 'bho', 'bih', 'bik', 'bin', 'bis', 'bla', 'bnt', 'tib (B)', 'bod (T)', 'bos', 'bra', 'bre', 'btk', 'bua', 'bug', 'bul', 'bur (B)', 'mya (T)', 'byn', 'cad', 'cai', 'car', 'cat', 'cau', 'ceb', 'cel', 'cze (B)', 'ces (T)', 'cha', 'chb', 'che', 'chg', 'chi (B)', 'zho (T)', 'chk', 'chm', 'chn', 'cho', 'chp', 'chr', 'chu', 'chv', 'chy', 'cmc', 'cnr', 'cop', 'cor', 'cos', 'cpe', 'cpf', 'cpp', 'cre', 'crh', 'crp', 'csb', 'cus', 'wel (B)', 'cym (T)', 'dak', 'dan', 'dar', 'day', 'del', 'den', 'ger (B)', 'deu (T)', 'dgr', 'din', 'div', 'doi', 'dra', 'dsb', 'dua', 'dum', 'dut (B)', 'nld (T)', 'dyu', 'dzo', 'efi', 'egy', 'eka', 'gre (B)', 'ell (T)', 'elx', 'eng', 'enm', 'epo', 'est', 'ewe', 'ewo', 'fan', 'fao', 'per (B)', 'fas (T)', 'fat', 'fij', 'fil', 'fin', 'fiu', 'fon', 'fre (B)', 'fra (T)', 'frm', 'fro', 'frr', 'frs', 'fry', 'ful', 'fur', 'gaa', 'gay', 'gba', 'gem', 'geo (B)', 'kat (T)', 'gez', 'gil', 'gla', 'gle', 'glg', 'glv', 'gmh', 'goh', 'gon', 'gor', 'got', 'grb', 'grc', 'grn', 'gsw', 'guj', 'gwi', 'hai', 'hat', 'hau', 'haw', 'heb', 'her', 'hil', 'him', 'hin', 'hit', 'hmn', 'hmo', 'hrv', 'hsb', 'hun', 'hup', 'iba', 'ibo', 'ice (B)', 'isl (T)', 'ido', 'iii', 'ijo', 'iku', 'ile', 'ilo', 'ina', 'inc', 'ind', 'ine', 'inh', 'ipk', 'ira', 'iro', 'ita', 'jav', 'jbo', 'jpn', 'jpr', 'jrb', 'kaa', 'kab', 'kac', 'kal', 'kam', 'kan', 'kar', 'kas', 'kau', 'kaw', 'kaz', 'kbd', 'kha', 'khi', 'khm', 'kho', 'kik', 'kin', 'kir', 'kmb', 'kok', 'kom', 'kon', 'kor', 'kos', 'kpe', 'krc', 'krl', 'kro', 'kru', 'kua', 'kum', 'kur', 'kut', 'lad', 'lah', 'lam', 'lao', 'lat', 'lav', 'lez', 'lim', 'lin', 'lit', 'lol', 'loz', 'ltz', 'lua', 'lub', 'lug', 'lui', 'lun', 'luo', 'lus', 'mac (B)', 'mkd (T)', 'mad', 'mag', 'mah', 'mai', 'mak', 'mal', 'man', 'mao (B)', 'mri (T)', 'map', 'mar', 'mas', 'may (B)', 'msa (T)', 'mdf', 'mdr', 'men', 'mga', 'mic', 'min', 'mis', 'mkh', 'mlg', 'mlt', 'mnc', 'mni', 'mno', 'moh', 'mon', 'mos', 'mul', 'mun', 'mus', 'mwl', 'mwr', 'myn', 'myv', 'nah', 'nai', 'nap', 'nau', 'nav', 'nbl', 'nde', 'ndo', 'nds', 'nep', 'new', 'nia', 'nic', 'niu', 'nno', 'nob', 'nog', 'non', 'nor', 'nqo', 'nso', 'nub', 'nwc', 'nya', 'nym', 'nyn', 'nyo', 'nzi', 'oci', 'oji', 'ori', 'orm', 'osa', 'oss', 'ota', 'oto', 'paa', 'pag', 'pal', 'pam', 'pan', 'pap', 'pau', 'peo', 'phi', 'phn', 'pli', 'pol', 'pon', 'por', 'pra', 'pro', 'pus', 'qaa-qtz', 'que', 'raj', 'rap', 'rar', 'roa', 'roh', 'rom', 'rum (B)', 'ron (T)', 'run', 'rup', 'rus', 'sad', 'sag', 'sah', 'sai', 'sal', 'sam', 'san', 'sas', 'sat', 'scn', 'sco', 'sel', 'sem', 'sga', 'sgn', 'shn', 'sid', 'sin', 'sio', 'sit', 'sla', 'slo (B)', 'slk (T)', 'slv', 'sma', 'sme', 'smi', 'smj', 'smn', 'smo', 'sms', 'sna', 'snd', 'snk', 'sog', 'som', 'son', 'sot', 'spa', 'srd', 'srn', 'srp', 'srr', 'ssa', 'ssw', 'suk', 'sun', 'sus', 'sux', 'swa', 'swe', 'syc', 'syr', 'tah', 'tai', 'tam', 'tat', 'tel', 'tem', 'ter', 'tet', 'tgk', 'tgl', 'tha', 'tig', 'tir', 'tiv', 'tkl', 'tlh', 'tli', 'tmh', 'tog', 'ton', 'tpi', 'tsi', 'tsn', 'tso', 'tuk', 'tum', 'tup', 'tur', 'tut', 'tvl', 'twi', 'tyv', 'udm', 'uga', 'uig', 'ukr', 'umb', 'und', 'urd', 'uzb', 'vai', 'ven', 'vie', 'vol', 'vot', 'wak', 'wal', 'war', 'was', 'wen', 'wln', 'wol', 'xal', 'xho', 'yao', 'yap', 'yid', 'yor', 'ypk', 'zap', 'zbl', 'zen', 'zgh', 'zha', 'znd', 'zul', 'zun', 'zxx', 'zza']
country_list = ['AF', 'AX', 'AL', 'DZ', 'AS', 'AD', 'AO', 'AI', 'AQ', 'AG', 'AR', 'AM', 'AW', 'AU', 'AT', 'AZ', 'BS', 'BH', 'BD', 'BB', 'BY', 'BE', 'BZ', 'BJ', 'BM', 'BT', 'BO', 'BQ', 'BA', 'BW', 'BV', 'BR', 'IO', 'BN', 'BG', 'BF', 'BI', 'CV', 'KH', 'CM', 'CA', 'KY', 'CF', 'TD', 'CL', 'CN', 'CX', 'CC', 'CO', 'KM', 'CG', 'CD', 'CK', 'CR', 'CI', 'HR', 'CU', 'CW', 'CY', 'CZ', 'DK', 'DJ', 'DM', 'DO', 'EC', 'EG', 'SV', 'GQ', 'ER', 'EE', 'ET', 'FK', 'FO', 'FJ', 'FI', 'FR', 'GF', 'PF', 'TF', 'GA', 'GM', 'GE', 'DE', 'GH', 'GI', 'GR', 'GL', 'GD', 'GP', 'GU', 'GT', 'GG', 'GN', 'GW', 'GY', 'HT', 'HM', 'VA', 'HN', 'HK', 'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IM', 'IL', 'IT', 'JM', 'JP', 'JE', 'JO', 'KZ', 'KE', 'KI', 'KP', 'KR', 'KW', 'KG', 'LA', 'LV', 'LB', 'LS', 'LR', 'LY', 'LI', 'LT', 'LU', 'MO', 'MK', 'MG', 'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MQ', 'MR', 'MU', 'YT', 'MX', 'FM', 'MD', 'MC', 'MN', 'ME', 'MS', 'MA', 'MZ', 'MM', 'NA', 'NR', 'NP', 'NL', 'NC', 'NZ', 'NI', 'NE', 'NG', 'NU', 'NF', 'MP', 'NO', 'OM', 'PK', 'PW', 'PS', 'PA', 'PG', 'PY', 'PE', 'PH', 'PN', 'PL', 'PT', 'PR', 'QA', 'RE', 'RO', 'RU', 'RW', 'BL', 'SH', 'KN', 'LC', 'MF', 'PM', 'VC', 'WS', 'SM', 'ST', 'SA', 'SN', 'RS', 'SC', 'SL', 'SG', 'SX', 'SK', 'SI', 'SB', 'SO', 'ZA', 'GS', 'SS', 'ES', 'LK', 'SD', 'SR', 'SJ', 'SZ', 'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ', 'TH', 'TL', 'TG', 'TK', 'TO', 'TT', 'TN', 'TR', 'TM', 'TC', 'TV', 'UG', 'UA', 'AE', 'GB', 'US', 'UM', 'UY', 'UZ', 'VU', 'VE', 'VN', 'VG', 'VI', 'WF', 'EH', 'YE', 'ZM', 'ZW']


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@sources.route('/')
def index():
    """Create sources index page."""
    scripts = ['js/parsley.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/corpus/dropzone.js', 'js/sources/sources.js', 'js/sources/upload.js']
    styles = []
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}]
    return render_template('sources/index.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)


@sources.route('/create', methods=['GET', 'POST'])
def create():
    """Create Sources manifest page."""
    scripts = ['js/parsley.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/sources/sources.js']
    styles = ['css/jquery-ui.css']
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/create', 'label': 'Create Publication'}]
    with open("app/templates/sources/template_config.yml", 'r') as stream:
        templates = yaml.load(stream)
    return render_template('sources/create.html', lang_list=lang_list, country_list=country_list, scripts=scripts, styles=styles, breadcrumbs=breadcrumbs, templates=templates)


@sources.route('/create-manifest', methods=['GET', 'POST'])
def create_manifest():
    """Create Sources manifests ajax route."""
    errors = []
    data = request.json
    # Ensure that the metapath is correct
    if not data['metapath'].startswith('Sources'):
        data['metapath'] = 'Sources,' + data['metapath']
    data['metapath'] = data['metapath'].strip(',')
    # Remove empty values
    manifest = {}
    for key, value in data.items():
        if value != '':
            manifest[key] = value

    # Validate the resulting manifest
    # print(json.dumps(manifest, indent=2, sort_keys=False))
    if methods.validate_manifest(manifest) is True:
        database_errors = methods.create_record(manifest)
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


@sources.route('/delete-manifest', methods=['GET', 'POST'])
def delete_manifest():
    """Delete Sources Ajax route."""
    errors = []
    name = request.json['name']
    metapath = request.json['metapath']
    result = methods.delete_source(name, metapath)
    response = {'errors': errors}
    if result == 'success':
        response['result'] = 'success'
    else:
        response['result'] = 'fail'
        errors.append(result)
    return json.dumps(response)


# Helpers for /display
def get_default_property(template, prop):
    """Return the first column key in the template for the specified property."""
    for tab in [template['source-template'][0]['required'], template['source-template'][1]['optional']]:
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


@sources.route('/display/<name>')
def display(name):
    """Display Sources page."""
    scripts = ['js/parsley.min.js', 'js/jquery-ui.js', 'js/moment.min.js', 'js/sources/sources.js']
    with open("app/templates/sources/template_config.yml", 'r') as stream:
        templates = yaml.load(stream)
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/display', 'label': 'Display Publication'}]
    errors = []
    manifest = {}
    try:
        manifest = sources_db.find_one({'name': name})
        with open("app/templates/sources/template_config.yml", 'r') as stream:
            templates = yaml.load(stream)
        # Reshape Lists
        for key, value in manifest.items():
            # The property is a list
            if isinstance(value, list):
                manifest[key] = reshape_list(key, value, templates)

        # Make sure the manifest has all template properties
        templates = templates['source-template']
        opts = [templates[0]['required'], templates[1]['optional']]
        for opt in opts:
            for prop in opt:
                if prop['name'] not in manifest and prop['fieldtype'] == 'text':
                    manifest[prop['name']] = ''
                if prop['name'] not in manifest and prop['fieldtype'] == 'textarea':
                    manifest[prop['name']] = ['']
    except:
        templates = []
        errors.append('Unknown Error: The manifest does not exist or could not be loaded.')
    return render_template('sources/display.html', lang_list=lang_list,
                           country_list=country_list, scripts=scripts,
                           breadcrumbs=breadcrumbs, manifest=manifest,
                           errors=errors, templates=templates)


@sources.route('/download-export/<filename>', methods=['GET', 'POST'])
def download_export(filename):
    """Trigger download and empty the temp folder."""
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


@sources.route('/search', methods=['GET', 'POST'])
def search():
    """Search Sources page."""
    scripts = ['js/parsley.min.js', 'js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/sources/sources.js', 'js/jquery-sortable-min.js', 'js/sources/search.js']
    styles = ['css/query-builder.default.css']
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/search', 'label': 'Search Sources'}]
    if request.method == 'GET':
        return render_template('sources/search.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs, result=[])
    if request.method == 'POST':
        # Default settings
        errors = []
        page_size = 5
        page_num = 1
        filters = {}
        limit = 0
        sort = [['name', 'ASC']]

        # Assemble request data
        if request.json['page']:
            page_num = int(request.json['page'])
        if request.json['query']:
            filters = request.json['query']
        if request.json['advancedOptions']['limit']:
            limit = int(request.json['advancedOptions']['limit'])
        sorting = []
        if request.json['advancedOptions']['sort']:
            sort = request.json['advancedOptions']['sort']
        for item in sort:
            if item[1] == 'ASC':
                opt = (item[0], pymongo.ASCENDING)
            else:
                opt = (item[0], pymongo.DESCENDING)
            sorting.append(opt)
        if request.json['advancedOptions']['show_properties'] != []:
            show_properties = request.json['advancedOptions']['show_properties']
        else:
            show_properties = None

        # Query the entire database
        query = sources_db.find(filters, projection=show_properties).limit(limit).sort(sorting)
        result = list(query)

        # Paginate the result
        pages, num_pages = methods.grouper(result, page_size, 0)

        # Filter the full query to just _ids on the requested page
        records = [doc for doc in result if str(doc['_id']) in pages[page_num]]

        # Remove the _id field if not requested
        if '_id' not in show_properties:
            for k, _ in enumerate(records):
                del records[k]['_id']

        # Check whether records can be returned
        if records == []:
            errors.append('No records were found matching your search criteria.')

        # Return the response
        response = {'response': records, 'errors': errors, 'num_pages': num_pages}
        return json.dumps(response, default=JSON_UTIL)


@sources.route('/export-manifest', methods=['GET', 'POST'])
def export_manifest():
    """Export a single manifest from the Display page."""
    if request.method == 'POST':
        errors = []
        result = sources_db.find_one(request.json)
        if not result:
            filename = ''
            errors.append('No records were found matching your search criteria.')
        # Need to write the results to temp folder
        else:
            filename = request.json['name'] + '.json'
            filepath = os.path.join('app/temp', filename)
            methods.make_dir('app/temp')
            with open(filepath, 'w') as f:
                f.write(json.dumps(result, indent=2, sort_keys=False, default=JSON_UTIL))
        return json.dumps({'filename': filename, 'errors': errors})


@sources.route('/export-search', methods=['GET', 'POST'])
def export_search():
    """Ajax route for exporting search results."""
    if request.method == 'POST':
        result, _, errors = methods.search_sources(request.json)
        if not result:
            errors.append('No records were found matching your search criteria.')
        # Need to write the results to temp folder
        methods.make_dir('app/temp')
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


@sources.route('/update-manifest', methods=['GET', 'POST'])
def update_manifest():
    """Ajax route for updating manifests."""
    errors = []
    data = request.json
    # Remove empty values
    manifest = {}
    for key, value in data.items():
        if value != '':
            manifest[key] = value
    # Validate the resulting manifest and update the record
    database_errors = methods.update_record(manifest)
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


@sources.route('/upload', methods=['GET', 'POST'])
def upload():
    """Save each file uploaded by the import function to the uploads folder.

    Currently supports only one file.
    """
    if request.method == 'POST':
        try:
            data = []
            file = request.files['files[]']
            if file and methods.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_to_save = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file_to_save = os.path.join('app', file_to_save)
                file.save(file_to_save)
                try:
                    manifests, errors = methods.import_manifests([filename])
                except:
                    errors = ['Unknown Error: Upload failed.']
                f = {
                    'name': filename,
                    'manifests': manifests,
                    'errors': errors
                }
                data.append(f)
                return json.dumps(data, default=JSON_UTIL)
        except:
            f = {
                'errors': ['Unknown Error: Upload failed.']
            }
            data.append(f)
            return json.dumps(data, default=JSON_UTIL)


@sources.route('/clear')
def clear():
    """Go to this page to quickly empty the database. Disable this for production."""
    sources_db.delete_many({})
    return 'success'
