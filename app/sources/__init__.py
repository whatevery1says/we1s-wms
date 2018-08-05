import os, tabulator, itertools, requests, json, re, shutil
import yaml
# For various solutions to dealing with ObjectID, see
# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
# If speed becomes an issue: https://github.com/mongodb-labs/python-bsonjs
from bson import BSON
from bson import json_util
JSON_UTIL = json_util.default

# from datetime import datetime
from jsonschema import validate, FormatChecker
# from tabulator import Stream
# import pandas as pd
# from tableschema_pandas import Storage
from flask import Blueprint, render_template, request, url_for, current_app
from werkzeug.utils import secure_filename

import pymongo
from pymongo import MongoClient

# Set up the MongoDB client, configure the databases, and assign variables to the "collections" 
client = MongoClient('mongodb://localhost:27017')
db = client.we1s
sources_db = db.Sources

sources = Blueprint('sources', __name__, template_folder='sources')

from app.sources.helpers import methods as methods

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
    """Sources index page."""
    scripts = [
    # 'js/jQuery-File-Upload-9.20.0/js/vendor/jquery.ui.widget.js', 
    # 'js/jQuery-File-Upload-9.20.0/js/jquery.iframe-transport.js', 
    # 'js/jQuery-File-Upload-9.20.0/js/jquery.fileupload.js',
    'js/corpus/dropzone.js',
    'js/sources/sources.js',
    'js/sources/upload.js',
    'js/dateformat.js',
    'js/jquery-ui.js'
    ]
    styles = []
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}]
    return render_template('sources/index.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)


@sources.route('/create', methods=['GET', 'POST'])
def create():
    """Create manifest page."""
    scripts = ['js/parsley.min.js', 'js/sources/sources.js', 'js/dateformat.js', 'js/jquery-ui.js', 'js/moment.min.js']
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/create', 'label': 'Create Publication'}]
    with open("app/templates/sources/template_config.yml", 'r') as stream:
        templates = yaml.load(stream)    
    return render_template('sources/create.html', lang_list=lang_list, country_list=country_list, scripts=scripts, breadcrumbs=breadcrumbs, templates=templates)


@sources.route('/create-manifest', methods=['GET', 'POST'])
def create_manifest():
    """ Ajax route for creating manifests."""
    properties = {'namespace': 'we1sv2.0', 'path': 'Sources'}
    errors = []
    for key, value in request.json.items():
        if key == 'date':
            ls = value.splitlines()
            dates = [x.strip() for x in ls]
            new_dates, error_list = methods.check_date_format(dates)
            errors = errors + error_list
            if new_dates  != []:
                properties[key] = new_dates
        elif key == 'notes':
            value = json.loads(value)
            notes = []
            for item in value:
                for k, v in item.items():
                    notes.append(v)
            properties[key] = notes
        elif key == 'authors':
            value = json.loads(value)
            # Convert evil properties from hidden fields to a list
            good_dict = {}
            good_list = []
            evil_props = {k for d in value for k in d.keys()}
            # Build a dict for each ID
            for item in evil_props:
                item = re.sub('[a-zA-Z]+', '', item)
                good_dict[item] = {}
            # Add the values to the good dict by ID
            for item in value:
                k = item.keys()
                property = list(k)[0]
                id = re.sub('[a-zA-Z]+', '', property)
                val = item[property]
                if property.startswith('authorName'):
                    property = 'name'
                if property.startswith('authorGroup'):
                    property = 'group'
                if property.startswith('authorOrg'):
                    property = 'organization'
                good_dict[id][property] = val
            # Convert any author names to strings and add the good_dict values to the list
            for k, v in good_dict.items():
                if len(good_dict[k]) == 1:
                    v = good_dict[k]['name']
                good_list.append(v)
            properties[key] = good_list
        elif key == 'keywords':
            properties[key] = [x.strip() for x in value.split(',')]
        elif isinstance(value, list):
            ls = value.splitlines()
            ls =  [x.strip() for x in ls]
            if ls != []:
                properties[key] = ls
        elif value != '' and value != ['']:
            properties[key] = value
    if methods.validate_manifest(properties) == True:
        validation_errors = methods.create_record(properties)
        errors = errors + validation_errors
    else:
        msg = '''A valid manifest could not be created with the 
        data supplied. Please check your entries against the 
        <a href="/schema" target="_blank">manifest schema</a>.''' 
        errors.append(msg)

    # Need to insert into the database
    manifest = json.dumps(properties, indent=2, sort_keys=False, default=JSON_UTIL)

    if len(errors) > 0:
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
    """ Ajax route for deleting manifests."""
    errors = []
    name = request.json['name']
    metapath = request.json['metapath']
    msg = methods.delete_source(name, metapath)
    if msg != 'success':
        errors.append(msg)
    return json.dumps({'errors': errors})


@sources.route('/display/<name>')
def display(name):
    """ Page for displaying Source manifests."""
    scripts = ['js/parsley.min.js', 'js/sources/sources.js']
    with open("app/templates/sources/template_config.yml", 'r') as stream:
        templates = yaml.load(stream)    
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/display', 'label': 'Display Publication'}]
    errors = []
    manifest = {}
    try:
        result = sources_db.find_one({'name': name})
        assert result != None
        for key, value in result.items():
            if isinstance(value, list):
                manifest[key] = []
                for element in value:
                    if isinstance(element, dict):
                        l = list(methods.NestedDictValues(element))
                        s = ', '.join(l)
                        manifest[key].append(s)
                    else:
                        manifest[key].append(element)
                manifest[key] = '\n'.join(manifest[key])
            else:
                manifest[key] = str(value)
    except:
        errors.append('Unknown Error: The manifest does not exist or could not be loaded.')
    return render_template('sources/display.html', lang_list=lang_list, 
        country_list=country_list, scripts=scripts, breadcrumbs=breadcrumbs,
        manifest=manifest, errors=errors, templates=templates)


@sources.route('/download-export/<filename>', methods=['GET', 'POST'])
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

'''
@sources.route('/search', methods=['GET', 'POST'])
def search():
    """ Page for searching Sources manifests."""
    scripts = ['js/parsley.min.js', 'js/jquery.twbsPagination.min.js', 'js/sources/sources.js']
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/search', 'label': 'Search Sources'}]
    if request.method == 'GET':
        return render_template('sources/search.html', scripts=scripts,
            breadcrumbs=breadcrumbs)
    if request.method == 'POST':
        result, num_pages, errors = methods.search_sources(request.json)
        return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)
        '''


@sources.route('/search', methods=['GET', 'POST'])
def search2():
    """ Experimental Page for searching sources manifests."""
    scripts = ['js/query-builder.standalone.js', 'js/moment.min.js', 'js/jquery.twbsPagination.min.js', 'js/sources/sources.js', 'js/jquery-sortable-min.js', 'js/sources/search.js', 'js/dateformat.js', 'js/jquery-ui.js']
    styles = ['css/query-builder.default.css']    
    breadcrumbs = [{'link': '/sources', 'label': 'Sources'}, {'link': '/sources/search', 'label': 'Search Sources'}]
    if request.method == 'GET':
        return render_template('sources/search2.html', scripts=scripts, styles=styles, breadcrumbs=breadcrumbs)
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
        result, num_pages, errors = methods.search_sources(query, limit, paginated, page, show_properties, sorting)
        # Don't show the MongoDB _id unless it is in show_properties
        if '_id' not in request.json['advancedOptions']['show_properties']:
            for k, v in enumerate(result):
                del result[k]['_id']
        if result == []:
            errors.append('No records were found matching your search criteria.')
        return json.dumps({'response': result, 'num_pages': num_pages, 'errors': errors}, default=JSON_UTIL)


@sources.route('/export-manifest', methods=['GET', 'POST'])
def export_manifest():
    """ Ajax route for exporting a single manifest from the Display page."""
    if request.method == 'POST':
        errors = []
        result = sources_db.find_one(request.json)
        if len(result) == 0:
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
    """ Ajax route for exporting search results."""
    if request.method == 'POST':
        result, num_pages, errors = methods.search_sources(request.json)
        if len(result) == 0:
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
    """ Ajax route for updating manifests."""
    properties = {'namespace': 'we1sv2.0', 'path': 'Sources'}
    errors = []
    for key, value in request.json.items():
        if key == 'date':
            ls = value.splitlines()
            dates = [x.strip() for x in ls]
            new_dates, error_list = methods.check_date_format(dates)
            errors = errors + error_list
            if new_dates  != []:
                properties[key] = new_dates
        elif isinstance(value, list):
            ls = value.splitlines()
            ls =  [x.strip() for x in ls]
            if ls != []:
                properties[key] = ls
        elif value != '' and value != ['']:
            properties[key] = value
    if methods.validate_manifest(properties) == True:
        validation_errors = methods.update_record(properties)
        errors = errors + validation_errors
    else:
        msg = '''A valid manifest could not be created with the 
        data supplied. Please check your entries against the 
        <a href="/schema" target="_blank">manifest schema</a>.''' 
        errors.append(msg)

    # Need to insert into the database
    manifest = json.dumps(properties, indent=2, sort_keys=False)
    if len(errors) > 0:
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
    """Ajax route saves each file uploaded by the import function
    to the uploads folder. Currently supports only one file.
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
    pass


@sources.route('/clear')
def clear():
    """ Going to this page will quickly empty the datbase.
    Disable this for production.
    """
    sources_db.delete_many({})
    return 'success'
