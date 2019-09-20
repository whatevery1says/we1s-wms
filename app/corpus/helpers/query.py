"""query.py."""

# import: standard
from itertools import zip_longest
# import: third-party
import pandas as pd

# Database info should be passed to the Query class,
# but the code below is retained in case it needs
# to be activated for testing.

# import pymongo
# from pymongo import MongoClient
# from pymongo.collation import Collation
# Set up the MongoDB client, configure the databases, and assign variables to the "collections"
# client = MongoClient('mongodb://localhost:27017')
# db = client.we1s
# corpus_db = db.Corpus
# client = MongoClient('mongodb://mongo:27017')
# DB has one collection, so treat it as the whole DB
# corpus_db = client.Corpus.Corpus

# ----------------------------------------------------------------------------#
# Query Class
# ----------------------------------------------------------------------------#

def paginate(iterable, page_size=10, padvalue=None, ids_only=False):
    """Separate query results into pages.

    Returns a dict with page numbers as keys and records as values.
    If `ids_only` is True, only the `_id numbers` (cast as strings)
    will be returned.
    """
    pages = {}
    groups = zip_longest(*[iter(iterable)]*page_size, fillvalue=padvalue)
    for i, group in enumerate(groups):
        if ids_only:
            pages[i + 1] = [str(item['_id']) for item in group if item is not 0]
        else:
            pages[i + 1] = [item for item in group if item is not 0]
    return pages, len(pages)

class Query:
    """Define object to obtain query results."""

    def __init__(self, client, db, collection_list, query, projection, sortby=None, limit=None, head=None, filters=None):
        """Initialise the object.

        client: A MongoDB client object
        db: The name of the database
        collection_list: A list of collection names
        query: A MongoDB query array
        projection: A list of keys to display in the results
        sortby: A list of tuples formatted (key, 'ASC'|'DESC') with the primary sort key first
        limit: A limit on the number of results *after* all results are returned
        head: A limit on the number of results returned from each collection before merging collections
              (mostly used for testing).
        filters: A list of collections by which to filter the results
              after retrieval. Probably not useful as is, but this
              function can be expanded later for more sophisticated
              querying.
        """
        # Check parameter data types
        try:
            assert isinstance(db, str)
        except:
            raise BaseException('The `db` parameter must be a string.')
        try:
            assert isinstance(collection_list, list)
        except:
            raise BaseException('The `collection_list` parameter must be a list or `None`.')
        if limit is None:
            limit = 0
        if head is None:
            head = 0
        try:
            assert isinstance(limit, int) or limit is None
        except:
            raise BaseException('The `limit` parameter must be an integer or `None`.')
        try:
            assert isinstance(sortby, list) or sortby is None
        except:
            raise BaseException('The `sortby` parameter must be a list or `None`.')
        try:
            assert isinstance(projection, list) or projection is None
            if projection == None:
                projection = ['_id', 'name']
            if sortby is not None:
                sort_keys = [key[0] for key in sortby]
                for key in sort_keys:
                    if key not in projection:
                        raise BaseException('The `sortby` parameter contains a field not in the `projection` list.')
            else:
                sort_keys = None
        except:
            raise BaseException('The `projection` parameter must be a list or `None`.')
        try:
            assert isinstance(filters, list) or filters is None
        except:
            raise BaseException('The `filters` parameter must be a list or `None`.')
        # Initialise object
        self.client = client
        self.db = db
        self.collection_list = collection_list
        self.limit = limit
        self.sortby = sortby
        self.sort_keys = sort_keys
        self.projection = projection
        self.head = head
        self.filters = filters
        self.large_query_size = 250000
        self.large_query = False
        self.query = query
        # Query initial results
        self.results = self._get_results()
        # if projection is not None:
        #     self.results = self._handle_projection(self.results, add_id=True)

    def _get_results(self):
        """Perform a query on multiple collections.

        Merges the results into a list of tuples.
        """
        results = []
        for collection in self.collection_list:
            corpus_db = self.client[self.db][collection]
            cursor = corpus_db.find(
                    self.query,
                    projection=self.projection,
                    limit=self.head
                )
            results.append((collection, cursor))
        if len(results) > self.large_query_size:
            self.large_query = True
        return results

    def _handle_projection(self, records, add_id=False, remove_collection=False):
        """Strip fields not in the projection list."""
        projection = self.projection
        if add_id and '_id' not in projection:
            projection.append('_id')
        for i, result in enumerate(records):
            for key in list(result.keys()):
                if key not in self.projection and key is not '_id' and key is not 'collection':
                    del records[i][key]
                if remove_collection:
                    del records[i]['collection']
        return records

    def get_result_table(self, sortby=None, filters=None, as_df=False):
        """Get the result set in a pandas dataframe.

        The table columns are _id, name, collection.
        """
        # Build the dataframe
        df = pd.DataFrame(columns=self.projection + ['collection'])
        for collection, cursor in self.results:
            for row in cursor:
                # Append the row
                row['collection'] = collection
                df = df.append(row, ignore_index=True)
            if self.filters is not None:
                df = df[df['collection'].isin(self.filters)]
        if self.sortby is not None:
            # Assign the sort order
            ascending = [True if key[1] == 'ASC' else False for key in self.sortby]
            df = df.sort_values(by=self.sort_keys, ascending=ascending)
        else:
            df = df.sort_values(by='name', ascending=False)

        # Return the dataframe
        if as_df:
            return df
        else:
            return df.to_dict('records')

    def get_records(self, sortby=None, projection=None, filters=None):
        """Perform a query on the result table.

        The input is a dataframe.
        The output is a list of dicts containing the merged records.
        """
        records = []
        df = self.get_result_table(sortby=sortby, filters=filters, as_df=True)
        unique_collections = list(set(df['collection'].values.tolist()))
        for collection in unique_collections:
            # Get a list of _ids for the collection
            filtered = df.loc[df['collection'] == collection]
            ids = filtered._id.values.tolist()
            # Now query the collection for the ids
            corpus_db = self.client[self.db][collection]
            if sortby is not None and self.large_query is not False:
                sorting = []
                for item in sortby:
                    if item[1] == 'ASC':
                        sorting.append((item[0], 1))
                    else:
                        sorting.append((item[0], -1))
                result = corpus_db.find({'_id': {'$in': ids}}, projection=projection).sort(sorting)
            else:
                result = corpus_db.find({'_id': {'$in': ids}}, projection=projection)
            for record in result:
                records.append(record)
        return records
