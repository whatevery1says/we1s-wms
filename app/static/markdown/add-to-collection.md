### Thought Experiment for Adding Data to New Collections

This is a thought experiment for how to go about adding data from one collection to another. The user would perform a search, and, when they received the results, they could click a button to add the results to a specified collection.

The button would bring up a form where the user could fill out the following fields:

- `target`: The path to the target collection
- `editors`: A list of names responsible for the addition
- `description`: A description of the query criteria

The WMS would additionally supply the following fields:

- `date`: The current datetime
- `query`: The query used to obtain the search results

This information would be used to compile a `processes` object, which would be appended to the collection manifest's list of `processes`.

The remaining challenge would be to extract the `source` collections from the query results and change the path in each manifest in the results before adding it to the new collection.

Here is some pseudo-code implementing the last part of this process:

```python
source = []
for result in results:
    # Add the record's collection _id to the source list
    collection = result['path'].split(',')[2]
    if collection not in source:
        source.append(collection)

        for result in results:
            # If the search result is a collection-level node
            if len(result['path'].split(',')) == 4:
                # Create a processes field, if necessary
                try:
                    assert test = result['processes']
                except:
                    result['processes] = []
                process = {
                    '_id': 'add_to_collection',
                    'path': 'WMS_internal_methods',
                    'description': 'Adds material from one collection to another.',
                    'editors': editors,
                    'source': source,
                    'steps': [
                        {
                            'type': 'WMS_add_to_collection',
                            'options': [
                                'query': query,
                                'target': target
                            ],
                            'description': description
                        }
                    ],
                    'date': date
                }
                # Append the process to the manifest
                result['processes].append(process)

    # For all record types, change the path to the new collection
    result[path] = re.sub(',Corpus,'.+,', ',Corpus,new_collection,',result[path])

    # Insert the record into the database
    insert_record(result)
```

The resulting `process` property should look something like this:

```json
{
  "_id": "add_to_collection",
  "path": "WMS_internal_methods",
  "description": "Adds material from one collection to another.",
  "editors": ["Scott Kleinman"],
  "source": ["new_york_times"],
  "steps": [
              {
               "type": "WMS_add_to_collection",
               "description": "User-supplied description of the query.",
                "options": [{
                    "query": "the_query",
                    "target": "the_target_collection"
                }]
              }
            ],
  "date": ["2018-03-03"]
}
```