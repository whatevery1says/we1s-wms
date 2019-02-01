/* global bootbox, hideProcessing, moment, showProcessing */
/* eslint no-undef: "error" */
var schema = [
  {
    'id': 'contributors',
    'label': 'contributors',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'content',
    'label': 'content',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'created',
    'label': 'created',
    'type': 'date',
    'validation': {
      'callback': function (value, rule) {
        var d = moment(value, 'YYYY-MM-DD', true).isValid()
        var dt = moment(value, 'YYYY-MM-DDTHH:mm:ss', true).isValid()
        if (d === true || dt === true) {
          return true
        } else {
          return ['<code>{0}</code> is not a valid date format. Please use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:mm:ss</code>.', value]
        }
      }
    }
  },
  {
    'id': 'description',
    'label': 'description',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'id',
    'label': 'id',
    'type': 'string',
    'size': 30
  },
  {
    'id': '_id',
    'label': '_id',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'image',
    'label': 'image',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'keywords',
    'label': 'keywords',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'label',
    'label': 'label',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'metapath',
    'label': 'metapath',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'name',
    'label': 'name',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'namespace',
    'label': 'namespace',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'licenses',
    'label': 'licenses',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'notes',
    'label': 'notes',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'resources',
    'label': 'resources',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'shortTitle',
    'label': 'shortTitle',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'title',
    'label': 'title',
    'type': 'string',
    'size': 30
  },
  {
    'id': 'updated',
    'label': 'updated',
    'type': 'date',
    'validation': {
      'callback': function (value, rule) {
        var d = moment(value, 'YYYY-MM-DD', true).isValid()
        var dt = moment(value, 'YYYY-MM-DDTHH:mm:ss', true).isValid()
        if (d === true || dt === true) {
          return true
        } else {
          return ['<code>{0}</code> is not a valid date format. Please use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:mm:ss</code>.', value]
        }
      }
    }
  },
  {
    'id': 'version',
    'label': 'version',
    'type': 'string',
    'size': 30
  }
]

// Query Builder options
var options = {
  allow_empty: true,
  filters: schema,
  default_filter: 'name',
  icons: {
    add_group: 'fa fa-plus-square',
    add_rule: 'fa fa-plus-circle',
    remove_group: 'fa fa-minus-square',
    remove_rule: 'fa fa-minus-circle',
    error: 'fa fa-exclamation-triangle'
  }
}

function addQueryBuilder () {
  /* Add the query builder to the DOM */
  let queryBuilderRow = '<div id="query-builder-row" class="form-group row"></div>'
  let queryBuilderCol = '<div id="query-builder-col" class="col-sm-10"><button id="test-query" class="btn btn-outline-editorial">Test Query</button><br></div>'
  $('#query-row').after(queryBuilderRow)
  $('#query-builder-row').append(queryBuilderCol)
  $('#query-builder-col').append('<div id="builder"></div>')
  $('#builder').queryBuilder(options)
}

function removeQueryBuilder () {
  /* Remove the query builder from the DOM */
  $('#query-builder-row').remove()
}

$(document).ready(function () {
  $('#update').click(function () {
    // If the user clicks edit and there is no datapackage, show the query builder
    if ($('#update').attr('title') === 'Edit Project' && $('#datapackage-row').length === 0) {
      addQueryBuilder()
    // This might not work. The function may have to be an ajax callback.
    } else {
      removeQueryBuilder()
    }
  })

  // When the Test Query button is clicked, validate and create a querystring
  $(document).on('click', '#test-query', function (e) {
    e.preventDefault()
    // var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    //var formvals = validateQuery([])
    var query = $('#builder').queryBuilder('getMongo')
    if (query == null) {
      bootbox.alert('Sorry, mate! You need to add a query value.')
    } else {
      $.ajax({
        method: 'POST',
        url: '/projects/test-query',
        data: JSON.stringify(query),
        contentType: 'application/json;charset=UTF-8',
        beforeSend: showProcessing()
      })
        .done(function (response) {
          hideProcessing()
          bootbox.alert(response)
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          hideProcessing()
          bootbox.alert({
            message: '<p>Sorry, mate! You\'ve got an error!</p>',
            callback: function () {
              return 'Error: ' + textStatus + ': ' + errorThrown
            }
          })
        })
    }
  })
})
