"""Statement for enabling the development environment."""

DEBUG = True
HOSTNAME = '0.0.0.0'
PORT = 5000
DEMO_MODE = True
UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
MONGO_CLIENT = 'mongodb://localhost:27017'

# Project Configurations
WORKSPACE_DIR = 'workspace/projects-wms'  # 'instance/workspace/projects-wms' on harbor
TEMPLATES_DIR = 'templates'
TEMP_DIR = 'temp'
WORKSPACE_URL = 'http://harbor.english.ucsb.edu:10000/tree/write/projects-wms/'
TEMPLATES = {
    'topic-modeling': 'topic_browser_json_template_2'
}
EXPORT_DIR = 'exports'
