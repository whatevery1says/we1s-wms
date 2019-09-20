/* global bootbox, moment */
$(document).ready(function () {
  var schema = [
    /* {
    'id': 'contributors',
    'label': 'contributors',
    'type': 'string',
    'size': 30
}, */
    /* {
    'id': 'content',
    'label': 'content',
    'type': 'string',
    'size': 30
}, */
    {
      'id': 'contentType',
      'label': 'contentType',
      'type': 'string',
      'size': 30
    },
    /* {
    'id': 'created',
    'label': 'created',
    'type': 'date',
    'validation': {
        'callback': function (value, rule) {
            var d = moment(value, 'YYYY-MM-DD', true).isValid();
            var dt = moment(value, 'YYYY-MM-DDTHH:mm:ss', true).isValid();
            if (d == true || dt == true) {
                return true;
            } else {
                return ['<code>{0}</code> is not a valid date format. Please use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:mm:ss</code>.', value];
            }
        }
    }
}, */
    {
      'id': 'description',
      'label': 'description',
      'type': 'string',
      'size': 30
    },
    /* {
    'id': 'documentType',
    'label': 'documentType',
    'type': 'string',
    'size': 30
}, */
    /* {
    'id': 'encoding',
    'label': 'encoding',
    'type': 'string',
    'size': 30
}, */
    /* {
    'id': 'format',
    'label': 'format',
    'type': 'string',
    'size': 30
}, */
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
    /* {
    'id': 'mediatype',
    'label': 'mediatype',
    'type': 'string',
    'size': 30
}, */
    {
      'id': 'name',
      'label': 'name',
      'type': 'string',
      'size': 30,
      'validation': {
        'callback': function (value, rule) {
          if (value !== '') {
            return true
          } else {
            return ('please enter name')
          }
        }
      }
    },
    {
      'id': 'namespace',
      'label': 'namespace',
      'type': 'string',
      'size': 30,
      'validation': {
        'callback': function (value, rule) {
          if (value !== '') {
            return true
          } else {
            return ('please enter namespace')
          }
        }
      }
    },
    /* {
    'id': 'licenses',
    'label': 'licenses',
    'type': 'string',
    'size': 30
}, */
    {
      'id': 'notes',
      'label': 'notes',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'country',
      'label': 'country',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'language',
      'label': 'language',
      'type': 'string',
      'size': 30
    },
    /* {
    'id': 'OCR',
    'label': 'OCR',
    'type': 'boolean',
    'size': 30,
    'input': 'radio',
    'values': [true, false],
    'operators': ['equal', 'not_equal']
}, */
    /* {
    'id': 'processes',
    'label': 'processes',
    'type': 'string',
    'size': 30
}, */
    {
      'id': 'publisher',
      'label': 'publisher',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'webpage',
      'label': 'webpage',
      'type': 'string',
      'size': 30
    },
    /* {
    'id': 'queryterms',
    'label': 'queryterms',
    'type': 'string',
    'size': 30
}, */
    /* {
    'id': 'relationships',
    'label': 'relationships',
    'type': 'string',
    'size': 30
}, */
    /* {
    'id': 'rights',
    'label': 'rights',
    'type': 'string',
    'size': 30
}, */
    {
      'id': 'shortTitle',
      'label': 'shortTitle',
      'type': 'string',
      'size': 30
    },
    /* {
    'id': 'sources',
    'label': 'sources',
    'type': 'string',
    'size': 30
}, */

    {
      'id': 'title',
      'label': 'title',
      'type': 'string',
      'size': 30,
      'validation': {
        'callback': function (value, rule) {
          if (value !== '') {
            return true
          } else {
            return ('please enter title')
          }
        }
      }
    },
    {
      'id': 'citation',
      'label': 'citation',
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
      'id': 'date',
      'label': 'date',
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
    },
    {
      'id': 'edition',
      'label': 'edition',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'tags',
      'label': 'tags',
      'type': 'string',
      'size': 30
    }
    /* {
    'id': 'workstation',
    'label': 'workstation',
    'type': 'string',
    'size': 30
} */
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

  // Instantiate the Query Builder
  $('#builder').queryBuilder(options)

  // When the Get Query button is clicked, validate and create a querystring
  $('#view-query, #search-query, #launch-jupyter').click(function () {
  // Remove previous error messages
    $('.has-error').find('.rule-actions > .error-message').remove()

    // If the form validates, build the querystring
    if ($('#builder').queryBuilder('validate')) {
      var querystring = JSON.stringify($('#builder').queryBuilder('getMongo'), undefined, 2)
      var advancedOptions = JSON.stringify(serialiseAdvancedOptions(), undefined, 2)
      var outputQueryString = JSON.stringify($('#builder').queryBuilder('getMongo'))
      var outputAdvancedOptions = JSON.stringify(serialiseAdvancedOptions())

      // Perform the search or display the query
      switch ($(this).attr('id')) {
        case 'search-query':
          //  bootbox.alert({
          // message: '<p>Ready to perform search.</p>'
          //  });
          sendQuery(querystring, advancedOptions)
          break
        case 'launch-jupyter':
          // Handle launch jupyter
          launchJupyter(querystring, advancedOptions)
          break
        default:
          let msg = '<p>Query:</p><pre><code>' + outputQueryString + '</code></pre>'
          msg += '<p>Advanced Options:</p><pre><code>' + outputAdvancedOptions + '</code></pre>'
          bootbox.alert({
            message: msg
          })
          break
      }
    } else {
      // Hack to display error messages.
      var message = $('.has-error').find('.error-container').attr('title')
      message = '<span class="error-message" style="margin-left:10px;">' + message + '</span>'
      $('.has-error').find('.rule-actions > button').parent().append(message)
    }

    /* Handles the Search Export feature */
    $('#exportSearchResults').click(function (e) {
      e.preventDefault()
      var querystring = JSON.stringify($('#builder').queryBuilder('getMongo'), undefined, 2)
      var advancedOptions = JSON.stringify(serialiseAdvancedOptions(), undefined, 2)
      let data = {
        'query': JSON.parse(querystring),
        'advancedOptions': JSON.parse(advancedOptions),
        'paginated': false
      }
      exportSearch(data)
    })
  })

  function sendQuery (query, advancedOptions, page = 1) {
    /* Searches the sources
      Input: Values from the search form
      Returns: An array containing results and errors for display
      */
    let data = {
      'query': JSON.parse(query),
      'page': page,
      'advancedOptions': JSON.parse(advancedOptions)
    }
    // console.log('Sending...')
    // console.log(data)
    $.ajax({
      method: 'POST',
      url: '/sources/search',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        // console.log('Done. Here is the response')
        $('#results').empty()
        response = JSON.parse(response)
        // console.log(response)
        if (response['errors'].length !== 0) {
          let result = response['errors']
          var message = ''
          $.each(result, function (i, item) {
            message += '<p>' + item + '</p>'
          })
          bootbox.alert({
            message: message
          })
        } else {
          let result = response['response']
          // Make the result into a string
          var out = ''
          $.each(result, function (i, item) {
            var link = '/sources/display/' + item['name']
            out += '<h4><a href="' + link + '">' + item['name'] + '</a></h4><br>'
            $.each(item, function (key, value) {
              value = JSON.stringify(value)
              if (key === 'content' && value.length > 200) {
                value = value.substring(0, 200) + '...'
              }
              // eval() removes the quotes around the string, which may or may not be desirable
              out += '<code>' + key + '</code>: ' + eval(value) + '<br>'
            })
            out += '<hr>'
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
          $('#hideSearch').removeClass('hidden')
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
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  }

  function launchJupyter (query, advancedOptions) {
    /* Sends the query to the code to launch a Jupyter notebook
      Input: Values from the search form
      Returns: An array containing results and errors for display
      */
    var page = 1
    let data = {
      'query': JSON.parse(query),
      'page': page,
      'advancedOptions': JSON.parse(advancedOptions)
    }
    $.ajax({
      method: 'POST',
      url: '/sources/launch-jupyter',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        if (response === 'error') {
          bootbox.alert({
            message: '<p>Unknown Error: A Jupyter notebook could not be launched. Make sure you have a Jupyter server running.</p>'
          })
        }
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p>',
          callback: function () {
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  }

  function exportSearch (data) {
    /* Exports the results of a sources search
           Input: Values from the search form
           Returns: An array containing results and errors for display */
    $.ajax({
      method: 'POST',
      url: '/sources/export-search',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        response = JSON.parse(response)
        if (response['errors'].length !== 0) {
          let result = JSON.stringify(response['errors'])
          bootbox.alert({
            message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>'
          })
        } else {
          window.location = '/sources/download-export/' + response['filename']
        }
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p>',
          callback: function () {
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  }

  /** ** Advanced Options Functions ****/
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

  // Serialise the data
  function serialiseAdvancedOptions () {
    // Declare an options object and helper variables
    var options = {'show_properties': [], 'sort': [], 'limit': 0}
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
        // var id = $(this).attr('data-id')
        var name = $(this).attr('data-name')
        var direction = $(this).attr('data-direction')
        // Append to the list of shown properties
        props.push(name)
        // Append name and direction to the list of sort criteria
        // Use an array that can be converted to a tuple
        if (direction !== 'none') {
          let tuplish = [name, direction]
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
  $('#serialise').click(function () {
    options = serialiseAdvancedOptions()
    // Display All Options
    console.log(JSON.stringify(options, null, 2))
    $('#allOpts').html('<pre>' + JSON.stringify(options, null, 2) + '</pre>')
  })
})
