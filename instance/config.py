"""Statement for enabling the development environment."""

DEBUG = True
HOSTNAME = '0.0.0.0'
PORT = 5000
DEMO_MODE = True
UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'

# Local Development Settings
# MONGO_CLIENT = 'mongodb://localhost:27017'
# SOURCES_DB = 'we1s'
# CORPUS_DB = 'we1s'
# PROJECTS_DB = 'we1s'

# Remote Server Settings
MONGO_CLIENT = 'mongodb://mongo:27017'
SOURCES_DB = 'Sources'
CORPUS_DB = 'we1s'
PROJECTS_DB = 'Projects'

# Project Configurations
WORKSPACE_DIR = 'workspace/projects-wms'  # 'instance/workspace/projects-wms' on harbor
TEMPLATES_DIR = 'templates'
TEMP_DIR = 'temp'
WORKSPACE_URL = 'http://harbor.english.ucsb.edu:10000/tree/write/projects-wms/'
TEMPLATES = {
    'topic-modeling': 'multiple_topics_template'
}
EXPORTS_DIR = 'exports'
