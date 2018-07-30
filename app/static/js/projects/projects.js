//
// General Helper Functions
//

function jsonifyForm () {
  /* Handles JSON form serialisation */
  var form = {}
  $.each($('form').serializeArray(), function (i, field) {
    form[field.name] = field.value || ''
  })
  return form
}

function validateQuery (requiredFields) {
  // Remove previous error messages
  $('.has-error').find('.rule-actions > .error-message').remove()

  // Serialise and validate the form values
  var formvals = jsonifyForm()

  // Make sure a query has been entered, then submit the query
  if (formvals['db-query'] === '') {
    bootbox.alert('Please enter a query.')
    return false
  } else {
    // Make sure all required fields are present
    var valid = true
    var invalid = []
    $.each(requiredFields, function (index, value) {
      if (formvals[value] === '') {
        valid = false
        invalid.push(value)
      }
    })
    if (valid === false) {
      var msg = '<p>Please enter values for the following fields:</p>'
      msg += '<ul>'
      $.each(invalid, function (index, value) {
        msg += '<li>' + value + '</li>'
      })
      msg += '</ul>'
      bootbox.alert(msg)
      return false
    } else {
      return formvals
    }
  }
}

//
// Project Methods
//

// General Save Function
function saveProject (action) {
  // Get the manifest, query, and action
  var manifest = validateQuery([]) // Returns form vals or false
  console.log(manifest)
  if (manifest !== false) {
    var data = {'action': action, 'query': manifest['db-query'], 'manifest': manifest}
    data = JSON.stringify(data)
    $.ajax({
      method: 'POST',
      url: '/projects/save-project',
      data: data,
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        if (JSON.parse(response)['result'] === 'fail') {
          var errors = JSON.parse(response)['errors']
          var msg = '<p>Could not save the project because of the following errors:</p><ul>'
          $.each(errors, function (index, value) {
            msg += '<li>' + value + '</li>'
          })
          msg += '</ul>'
        } else {
          $('#save').attr('title', 'Update Project')
          $('#save').attr('data-action', 'update')
          msg = '<p>The project was saved.</p>'
        }
        bootbox.alert({
          message: msg
        })
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>The project could not be updated because of the following errors:</p>'+response,
          callback: function () {
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  } else {
    bootbox.alert('Your form input could not be validated.')
  }
}

// General Delete Function
function deleteProject (name) {
  var manifest = jsonifyForm()
  var data = {
    'action': 'delete',
    'manifest': manifest,
    'query': "{'name': name, 'metapath': 'Projects'}"
  }
  $.ajax({
    method: 'POST',
    url: '/projects/delete-project',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      if (JSON.parse(response)['result'] === 'fail') {
        var errors = JSON.parse(response)['errors']
        var msg = '<p>Could not delete the project because of the following errors:</p><ul>'
        $.each(errors, function (index, value) {
          msg += '<li>' + value + '</li>'
        })
        msg += '</ul>'
        bootbox.alert(msg)
      } else {
        bootbox.alert('<p>The project was deleted.</p>')
        alert('Go home')
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The project could not be deleted because of the following errors:</p>'+response,
        callback: function () {
          return 'Error: ' + textStatus + ': ' + errorThrown
        }
      })
    })
}

// General Export Function
function exportProject () {
  // Get the manifest, query, and action
  var manifest = validateQuery(['name']) // Returns form vals or false
  if (manifest !== false) {
    var data = {'action': 'export', 'query': manifest['db-query'], 'manifest': manifest}
    data = JSON.stringify(data)
    $.ajax({
      method: 'POST',
      url: '/projects/export-project',
      data: data,
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        if (JSON.parse(response)['result'] === 'fail') {
          var errors = JSON.parse(response)['errors']
          var msg = '<p>Could not save the project because of the following errors:</p><ul>'
          $.each(errors, function (index, value) {
            msg += '<li>' + value + '</li>'
          })
          msg += '</ul>'
        } else {
          var downloadPath = JSON.parse(response)['key'] + '#' + manifest['name'] + '.zip'
          window.location = '/projects/download-export/' + downloadPath
        }
        bootbox.alert({
          message: msg
        })
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>The project could not be updated because of the following errors:</p>'+response,
          callback: function () {
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  } else {
    bootbox.alert('Your form input could not be validated.')
  }
}

// Launch Jupyter Function
function launchJupyter (btnId, formvals) {
  /* Sends the information needed to launch a Jupyter notebook
  Input: The notebook to launch and the values from the search form
  Returns: An array containing results and errors for display
  */
  var data = {
    'notebook': btnId,
    'manifest': formvals
  }
  console.log('Sending')
  $.ajax({
    method: 'POST',
    url: '/projects/launch-jupyter',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      console.log('Done')
      console.log(response)
      response = JSON.parse(response)
      if (response.result === 'fail') {
        var msg = '<p>Could not launch the virtual workspace because of the following errors:</p>'
        msg += '<ul>'
        $.each(response.errors, function (index, value) {
          msg += '<li>' + value + '</li>'
        })
        msg += '</ul>'
        bootbox.alert({
          message: msg
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

//
// $(document).ready()
//

$(document).ready(function () {
  // Handle the Display form on the index page
  $('#go').click(function (e) {
    var name = $('#display').val()
    window.location = '/projects/display/' + name
  })
  $('#display').on('keypress', function (e) {
    var key = (e.keyCode || e.which)
    if (key === 13 || key === 3) {
      $('#go').click()
    }
  })

  // Preview Show and Hide Buttons
  $('#preview').click(function (e) {
    e.preventDefault()
    $('form').hide()
    $('#previewDisplay').show()
    var jsonform = jsonifyForm($('#manifestForm'))
    $('#manifest').html(JSON.stringify(jsonform, null, '  '))
  })
  $('#hide').click(function (e) {
    e.preventDefault()
    $('#previewDisplay').hide()
    $('form').show()
  })

  // Save Button
  $('#save').click(function (e) {
    e.preventDefault()
    var outputQueryString = JSON.stringify($('#builder').queryBuilder('getMongo'))
    $('#db-query').val(outputQueryString)
    saveProject($(this).attr('data-action'))
  })

  // Delete Button
  $('#delete').click(function (e) {
    e.preventDefault()
    var name = $('#name').val()
    if (name !== '') {
      bootbox.confirm({
        message: 'Are you sure you wish to delete <code>' + name + '</code>?',
        buttons: {
          confirm: {label: 'Yes', className: 'btn-success'},
          cancel: {label: 'No', className: 'btn-danger'}
        },
        callback: function (result) {
          if (result === true) {
            deleteProject(name)
          }
        }
      })
    } else {
      bootbox.alert('Please enter a value for <code>name</code>.')
    }
  })

  // Export Button
  $('#export').click(function (e) {
    e.preventDefault()
    exportProject()
  })

  // Rocket Buttons
  $('.dropdown-item').click(function () {
    var btnId = $(this).attr('id').replace('-btn', '')
    var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    var formvals = validateQuery(requiredFields)
    if (formvals !== false) {
      launchJupyter(btnId, formvals)
    }
  })
}) /* End $(document).ready() */
