"""database.py."""

from bson import BSON
from bson import json_util
import pymongo
from pymongo import MongoClient

class DB:
    """Create database object."""

    def __init__(self, uri, sources, corpus, projects):
        """Initialise the client."""
        self.client = MongoClient(uri)
        self.sources = sources
        self.corpus = corpus
        self.projects = projects
