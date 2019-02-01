/* global bootbox, hideProcessing, moment, showProcessing */
/* eslint no-undef: "error" */
//
// General Helper Functions
//

// Serialise the data
function serialiseAdvancedOptions () {
  // Declare an options object and helper variables
  var options = {'show_properties': [], 'sort': [], 'limit': 0}
  var rows = []
  var props = []
  var sortList = []

  // Get the limit value and make sure it's a number
  var limit = parseInt($('#limit').val())
  if (isNaN(limit)) {
    limit = 0
  }

  // Gather data on all shown rows
  $.each($('tbody > tr'), function () {
    var show = $(this).attr('data-show')
    if (show === 'true') {
      var id = $(this).attr('data-id')
      var name = $(this).attr('data-name')
      var direction = $(this).attr('data-direction')
      // Append to the list of shown properties
      props.push(name)
      // Append name and direction to the list of sort criteria
      // Use an array that can be converted to a tuple
      if (direction !== 'none') {
        var tuplish = [name, direction]
        sortList.push(tuplish)
      }
    }
  })

  // Update the options object
  options['show_properties'] = props
  options['sort'] = sortList
  options['limit'] = limit

  return options
}

function sendQuery (query, advancedOptions, page = 1) {
/* Searches the Corpus
   Input: Values from the search form
   Returns: An array containing results and errors for display
   */
  var data = {
    'query': JSON.parse(query),
    'page': page,
    'advancedOptions': JSON.parse(advancedOptions)
  }
  $.ajax({
    method: 'POST',
    url: '/projects/search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      $('#results').empty()
      response = JSON.parse(response)
      if (response['errors'].length !== 0) {
        var result = response['errors']
        var message = ''
        $.each(result, function (i, item) {
          message += '<p>' + item + '</p>'
        })
        bootbox.alert({
          message: message
        })
      } else {
        result = response['response']
        // Make the result into a string
        var out = ''
        $.each(result, function (i, item) {
          var itemId = item['_id']['$oid']
          out += '<div id="result-' + itemId + '">'
          var link = '/projects/display/' + itemId
          var id = 'delete-' + itemId
          out += '<div style="margin-bottom:8px;"><h4 style="display: inline">' + item['name'] + '</h4> '
          out += '<a role="button" href="' + link + '" id="edit" class="btn btn-sm btn-outline-editorial" title="Edit Project" data-action="edit"><i class="fa fa-pencil"></i></a> '
          out += '<a role="button" id="' + id + '" class="btn btn-sm btn-outline-editorial delete-btn" title="Delete Project" data-action="delete"><i class="fa fa-trash"></i></a>'
          out += '</div>'
          $.each(item, function (key, value) {
            value = JSON.stringify(value)
            out += '<code>' + key + '</code>: ' + value + '<br>'
          })
          out += '<hr></div>'
        })
        var $pagination = $('#pagination')
        // Get the limit value and make sure it's a number
        var limit = parseInt($('#limit').val())
        if (isNaN(limit)) {
          limit = 0
        }
        var defaultOpts = {
          visiblePages: 5,
          initiateStartPageClick: false,
          onPageClick: function (event, page) {
            sendQuery(query, advancedOptions, page)
            $('#scroll').click()
          }
        }
        var totalPages = parseInt(response['num_pages'])
        var currentPage = $pagination.twbsPagination('getCurrentPage')
        $pagination.twbsPagination('destroy')
        $pagination.twbsPagination($.extend({}, defaultOpts, {
          startPage: currentPage,
          totalPages: totalPages
        }))
        $('#results').append(out)
        $('#hideSearch').html('Show Form')
        $('#exportSearchResults').show()
        $('#search-form').hide()
        $('#results').show()
        $('#pagination').show()
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

// Export Search Results Function
function exportSearchResults (data) {
  /* Exports the results of a search of the Projects database.
     Input: Values from the search form
     Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/projects/export-search-results',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      response = JSON.parse(response)
      if (response['errors'].length !== 0) {
        var result = JSON.stringify(response['errors'])
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>',
          callback: function () {
            ('Error: ' + textStatus + ': ' + errorThrown)
          }
        })
      } else {
        window.location = '/projects/download-export/search-results.zip'
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

//
// $(document).ready()
//

$(document).ready(function () {
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

  // Check whether the page is create, display, or search
  var pageType = window.location.pathname.split('/')[2]
  // Instantiate the Query Builder
  if (pageType !== 'display') {
    $('#builder').queryBuilder(options)
  }
  if (dbQuery !== '') {
    $('#builder').queryBuilder('setRulesFromMongo', dbQuery)
    $('#db-query').val(JSON.stringify(dbQuery))
  }

  // Update the query textarea when the query builder changes
  $('#builder').change(function () {
    var outputQueryString = JSON.stringify($('#builder').queryBuilder('getMongo'))
    $('#db-query').html(outputQueryString)
  })

  // When the Test Query button is clicked, validate and create a querystring
  $('#test-query').click(function (e) {
    e.preventDefault()
    var query = $('#builder').queryBuilder('getMongo')
    if (query == null) {
      bootbox.alert('Please supply values for the fields indicated in order to form a valid query.')
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

  // When the Get Query button is clicked, validate and create a querystring
  $('#view-query, #search').click(function () {
    // Remove previous error messages
    $('.has-error').find('.rule-actions > .error-message').remove()
    // If the form validates, build the querystring
    if ($('#builder').queryBuilder('validate')) {
      var querystring = JSON.stringify($('#builder').queryBuilder('getMongo'), undefined, 2)
      var advancedOptions = JSON.stringify(serialiseAdvancedOptions(), undefined, 2)
      var outputQueryString = JSON.stringify($('#builder').queryBuilder('getMongo'))
      var outputAdvancedOptions = JSON.stringify(serialiseAdvancedOptions())
      // Perform the search or display the query
      if ($(this).attr('id') == 'search') {
        sendQuery(querystring, advancedOptions)
      } else {
        var msg = '<p>Query:</p><pre><code>' + outputQueryString + '</code></pre>'
        msg += '<p>Advanced Options:</p><pre><code>' + outputAdvancedOptions + '</code></pre>'
        bootbox.alert({
          message: msg
        })
      }
    } else {
      // Hack to display error messages.
      var message = $('.has-error').find('.error-container').attr('title')
      message = '<span class="error-message" style="margin-left:10px;">' + message + '</span>'
      $('.has-error').find('.rule-actions > button').parent().append(message)
    }
  })

  // Handle the Serialise Button
  $('#serialise').click(function () {
    options = serialiseAdvancedOptions()
    // Display All Options
    console.log(JSON.stringify(options, null, 2))
    $('#allOpts').html('<pre>' + JSON.stringify(options, null, 2) + '</pre>')
  })

  // Toggles Show/Hide Form Button
  $('#hideSearch').click(function () {
    if ($('#hideSearch').html() == 'Hide Form') {
      $('#search-form').hide()
      $('#results').show()
      $('#pagination').show()
      $('#hideSearch').html('Show Form')
    } else {
      $('#hideSearch').html('Hide Form')
      $('#results').hide()
      $('#pagination').hide()      
      $('#search-form').show()
    }
  })

  /* Advanced Options Functions */

  // Make the table rows sortable
  $('.sorted_table').sortable({
    containerSelector: 'table',
    itemPath: '> tbody',
    itemSelector: 'tr',
    placeholder: '<tr class="placeholder"/>'
  })

  // Transfer the checked value to the row element
  $('.show').change(function () {
    var show = $(this).is(':checked')
    $(this).parent().parent().parent().attr('data-show', show)
  })

  // Transfer the sort value to the row element
  $('.direction').change(function () {
    var direction = $(this).val()
    $(this).parent().parent().attr('data-direction', direction)
  })

  // Export Search Results Button
  $('#exportSearchResults').click(function (e) {
    e.preventDefault()
    var querystring = JSON.stringify($('#builder').queryBuilder('getMongo'), undefined, 2)
    var advancedOptions = JSON.stringify(serialiseAdvancedOptions(), undefined, 2)
    var data = {
      'query': JSON.parse(querystring),
      'advancedOptions': JSON.parse(advancedOptions),
      'paginated': false
    }
    exportSearchResults(data)
  })

  // Search Results Delete Button
  $(document).on('click', '.delete-btn', function (e) {
    e.preventDefault()
    var id = $(this).attr('id')
    var _id = id.replace(/^delete-/, '')
    // alert('remove ' + _id)
    bootbox.confirm({
      message: 'Are you sure you wish to permanently delete project <code>' + _id + '</code>?',
      buttons: {
        confirm: {label: 'Yes', className: 'btn-success'},
        cancel: {label: 'No', className: 'btn-danger'}
      },
      callback: function (result) {
        if (result === true) {
          var data = {}
          data['action'] = 'delete'
          data['manifest'] = {'_id': _id, 'metapath': 'Projects'}
          data['query'] = JSON.stringify(data['manifest'])
          $.ajax({
            method: 'POST',
            url: '/projects/delete-project',
            data: JSON.stringify(data),
            contentType: 'application/json;charset=UTF-8',
            beforeSend: showProcessing()
          })
            .done(function (response) {
              hideProcessing()
              if (JSON.parse(response)['result'] === 'fail') {
                var errors = JSON.parse(response)['errors']
                var msg = '<p>Could not delete the project because of the following errors:</p><ul>'
                $.each(errors, function (index, value) {
                  msg += '<li>' + value + '</li>'
                })
                msg += '</ul>'
                bootbox.alert(msg)
              } else {
                $('#result-' + _id).remove()
                bootbox.alert('<p>The project was deleted.</p>')
              }
            })
            .fail(function (jqXHR, textStatus, errorThrown) {
              hideProcessing()
              bootbox.alert({
                message: '<p>The project could not be updated because of the following errors:</p>'+response,
                callback: function () {
                  return 'Error: ' + textStatus + ': ' + errorThrown
                }
              })
            })
        }
      }
    })
  })
})
