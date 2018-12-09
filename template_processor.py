"""template_processor.py."""

# Python imports
import json
import os
import yaml
from bs4 import BeautifulSoup

# Load the manifest
manifest = {
    '_id': '5adb5eb7f81fc912106bb9b3',
    'name': 'guardian',
    'metapath': 'Corpus',
    'namespace': 'we1sv2.0',
    'title': 'The Guardian',
    'sources': [{'title': 'The Guardian', 'path': 'Sources,guardian'}],
    'contributors': [{'title': 'Scott Kleinman'}],
    'created': [{'start': '2001-01-02', 'end': '2001-02-02'}]
}

# Load the template properties
with open("C:/Users/Scott/Documents/GitHub/whatevery1says/we1s-wms/app/templates/corpus/template_config.yml", 'r') as stream:
    templates = yaml.load(stream)
collection_template = templates['collection-template']
required = collection_template[0]['required']
optional = collection_template[1]['optional']
tabs = [required, optional]

# Loop through the tabs and process the templates
for tab in tabs:
    tab_properties = process_template(tab, manifest)
    print(tab_properties)

def process_template(template, manifest_dict):
    """Process each property in the tab template and create a UI element."""
    ui_elements = []
    for yaml_property in template:
        # Assign the property a value from the manifest or an empty value
        try:
            yaml_property['manifest_value'] = manifest_dict[yaml_property]
        except KeyError:
            if yaml_property['fieldtype'] == 'array':
                yaml_property['manifest_value'] = []
            else:
                yaml_property['manifest_value'] = ''
        # Instantiate a UI Property
        ui_property = UIProperty(yaml_property)
        if yaml_property['cloneable']:
            element = ui_property.multiple_rows()
        else:
            element = ui_property.single_row()
        ui_elements.append(element)
    return ui_elements

class UIProperty(object):
    """Create a UI element for a template property."""

    def __init__(self, yaml_property):
        """Class variables."""
        self.property = yaml_property
        self.name = yaml_property['name']
        self.value = yaml_property['manifest_value']
        self.fieldtype = yaml_property['fieldtype']
        self.required = yaml_property['required'] if 'required' in yaml_property else ''
        self.placeholder = yaml_property['placeholder'] if 'placeholder' in yaml_property else ''

    @staticmethod
    def create_row_div(obj):
        """Create a row div."""
        soup = BeautifulSoup('<body></body>', 'html.parser')
        # Instantiate the div with @class
        row = soup.new_tag('div')
        row['class'] = 'form-group-row'
        # Append a label with @class, @for, a string value
        label = soup.new_tag('label')
        label['class'] = 'col-sm-2 col-form-label'
        label['for'] = obj.name
        label.string = obj.name
        row.append(label)
        # Instantiate a div for the form field column with @class
        input_column = soup.new_tag('div')
        input_column['class'] = 'col-sm-10'
        # Add a form field with attributes and value
        input_tag = soup.new_tag('input')
        input_tag['type'] = obj.fieldtype
        input_tag['class'] = 'form-control'
        input_tag['name'] = obj.name
        input_tag['id'] = obj.name
        for prop in ['placeholder', 'required']: # 'readonly', 'disabled'
            if prop in obj:
                input_tag[prop] = obj.prop
        # Change arrays csv, if necessary, before adding the value
        if isinstance(obj.manifest_value, list):
            input_tag['value'] = ', '.join(obj.manifest_value)
        else:
            input_tag['value'] = joinobj.manifest_value
        # Add the form field to the column, the column to the row, the row to the div
        input_column.append(input_tag)
        row.append(input_column)
        soup.body.append(row)
        # Return the div as a string
        return soup.div.prettify()

    def single_row(self):
        """Create a single row."""
        row = self.create_row_div(self.name, self.soup)
        return row

    def multiple_rows(self):
        """Create multiple rows."""
        return self.property
   