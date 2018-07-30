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


function serialiseTextareas (cls) {
  var values = []
  $(cls).each(function () {
    var item = {}
    if (this.value !== '') {
      item[$(this).attr('id')] = this.value
      values.push(item)
    }
  })
  return JSON.stringify(values)
  }

function cleanup () {
  const form = jsonifyForm()
  const newform = {}
  const exclude = ['licenseName', 'licensePath', 'licenseTitle', 'notesField']
  // Clone the form values, ommitting empty fields and exclusions
  $.each(form, function (key, value) {
    if (value !== '' && value !== [] && $.inArray(key, exclude) === -1) {
      newform[key] = value
    }
  })
  // Convert comma-separated values to arrays
  const csvs = ['keywords']
  for (const property of csvs) {
    // Only process defined properties
    if (typeof newform[property] !== 'undefined') {
      newform[property] = newform[property].trim().split(/\s*,\s*/)
    }
  }

  // Convert arrays stored as hidden input string values
  const arrays = ['notes']
  for (const property of arrays) {
    newform[property] = eval(newform[property])
    // Only process defined properties
    if (typeof newform[property] !== 'undefined') {
      const list = []
      $.each(newform[property], function (key, value) {
        $.each(value, function (k, v) {
          list.push(v)
        })
      })
      newform[property] = list
    }
  }
  // Convert objects stored as hidden input string values
  const objects = ['licenses']
  for (var property of objects) {
    newform[property] = eval(newform[property])
    // Only process defined properties
    if (typeof newform[property] !== 'undefined') {
      // Convert evil properties from hidden fields to a list
      let goodDict = {}
      let goodList = []
      let evilProps = []
      // Get the property keys
      $.each(newform[property], function (key, value) {
        $.each(value, function (k, v) {
          evilProps.push(k)
        })
      })
      // Build object for each ID
      $.each(evilProps, function (key, item) {
        item = item.replace(/[a-zA-Z]+/, '')
        goodDict[item] = {}
      })
      // Add the values to the good dict by ID
      $.each(newform[property], function (i, item) {
        let obj = newform[property][i]
        let k = Object.keys(obj)
        let prop = k[0]
        let id = prop.replace(/[a-zA-Z]+/, '')
        let val = item[prop]
        if (prop.startsWith('licenseName')) {
          prop = 'name'
          goodDict[id][prop] = val
        }
        if (prop.startsWith('licenseTitle')) {
          prop = 'title'
          goodDict[id][prop] = val
        }
        if (prop.startsWith('licensePath')) {
          prop = 'path'
          goodDict[id][prop] = val
        }
      })
      // Convert any license names to strings and add the good_dict values to the list
      $.each(goodDict, function (k, v) {
        if (goodDict[k].length === 1) {
          v = goodDict[k]['name']
        } else {
          goodList.push(v)
        }
      })
      newform[property] = goodList
    }
  }
  return newform
}
  $(document).on('click', '.add-license', function () {
    // Keep count of the number of fields in session storage
    if ('licenseCount' in sessionStorage) {
      var count = parseInt(sessionStorage.getItem('licenseCount')) + 1
      sessionStorage.setItem('licenseCount', count.toString())
    } else {
      count = 0
      sessionStorage.setItem('licenseCount', '0')
    }
    // Show the remove icon
    $(this).next().removeClass('hidden')
    // Clone the template
    var $template = $('#licenses-template').clone()
    $(this).closest('.row').after($template.html())
    $('.licenseName').last().attr('id', 'licenseName' + count).removeClass('.licenseName')
    $('.licensePath').last().attr('id', 'licensePath' + count).removeClass('.licensePath')
    $('.licenseTitle').last().attr('id', 'licenseTitle' + count).removeClass('.licenseTitle')
    // Serialise the textareas and save the string to the hidden licenses field
    var serialisedTextareas = serialiseTextareas('.license-field')
    $('#licenses').val(serialisedTextareas)
    // console.log($('#licenses').val())
  })

  $(document).on('click', '.remove-license', function () {
    // If the field to remove is the only one, clone a new one
    // NB. There are three sub-fields
    if ($('.license-field').length === 3) {
      var count = parseInt(sessionStorage.getItem('licenseCount')) + 1
      sessionStorage.setItem('licenseCount', count.toString())
      var $template = $('#licenses-template').clone()
      $(this).closest('.row').after($template.html())
      $('.licenseName').last().attr('id', 'licenseName' + count).removeClass('.licenseName')
      $('.licensePath').last().attr('id', 'licensePath' + count).removeClass('.licensePath')
      $('.licenseTitle').last().attr('id', 'licenseTitle' + count).removeClass('.licenseTitle')
    }
    // Remove the license field
    $(this).parent().parent().remove()
    // Display the "licenses" label
    $('.license-field').eq(0).parent().prev().text('licenses')
    // Serialise the textareas and save the string to the hidden licenses field
    var serialisedTextareas = serialiseTextareas('.license-field')
    $('#licenses').val(serialisedTextareas)
    // console.log($('#licenses').val())
  })
  //can probably give all
  $(document).on('blur', '.license-field', function () {
    // Re-serialise the text areas when the user clicks on another element
    var serialisedTextareas = serialiseTextareas('.license-field')
    $('#licenses').val(serialisedTextareas)
    // console.log($('#licenses').val())
  })


  $(document).on('click', '.add-note', function () {
    if ('noteCount' in sessionStorage) {
      var count = parseInt(sessionStorage.getItem('noteCount')) + 1
      sessionStorage.setItem('noteCount', count.toString())
    } else {
      count = 0
      sessionStorage.setItem('noteCount', '0')
    }
    $(this).next().removeClass('hidden')
    var $template = $('#notes-template').clone()
    $(this).closest('.row').after($template.html())
    $('.note-field').last().attr('id', 'note' + count)
    var serialisedTextareas = serialiseTextareas('.note-field')
    $('#notes').val(serialisedTextareas)
    // console.log($('#notes').val())
  })

  $(document).on('click', '.remove-note', function () {
    if ($('.note-field').length === 1) {
      var count = parseInt(sessionStorage.getItem('noteCount')) + 1
      sessionStorage.setItem('noteCount', count.toString())
      var $template = $('#notes-template').clone()
      $(this).closest('.row').after($template.html())
      $('.note-field').last().attr('id', 'note' + count)
    }
    $(this).parent().parent().remove()
    $('.note-field').eq(0).parent().prev().text('notes')
    var serialisedTextareas = serialiseTextareas('.note-field')
    $('#notes').val(serialisedTextareas)
    // console.log($('#notes').val())
  })

  $(document).on('blur', '.note-field', function () {
    var serialisedTextareas = serialiseTextareas('.note-field')
    $('#notes').val(serialisedTextareas)
    // console.log($('#notes').val())
  })
  // End Property Cloning

//
// Script Methods
//

// General Save Function
function saveScript(action) {
  // Get the manifest, query, and action
    var manifest = validateQuery([]) // Returns form vals or false 
    if (manifest !== false) {
      var data = {'action': action, 'query': manifest['db-query'], 'manifest': manifest}
      data = JSON.stringify(data)
      $.ajax({
        method: 'POST',
        url: '/scripts/save-script',
        data: data,
        contentType: 'application/json;charset=UTF-8'
      })
      .done(function (response) {
        if (JSON.parse(response)['result'] == 'fail') {
          var errors = JSON.parse(response)['errors']
          var msg = '<p>Could not save the script because of the following errors:</p><ul>'
          $.each(errors, function (index, value) {
            msg += '<li>' + value + '</li>'
          })
          msg += '</ul>'
        } else {
          $('#save').attr('title', 'Update Script')
          $('#save').attr('data-action', 'update')
          msg = '<p>The script was saved.</p>'
        }
        bootbox.alert({
          message: msg
        })
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>The script could not be updated because of the following errors:</p>'+response,
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
function deleteScript(name) {
  var manifest = jsonifyForm()
  var data = {
    'action': 'delete',
    'manifest': manifest,
    'query': "{'name': name, 'metapath': 'Scripts'}"
  }
  $.ajax({
    method: 'POST',
    url: '/scripts/delete-script',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
  .done(function (response) {
    if (JSON.parse(response)['result'] == 'fail') {
      var errors = JSON.parse(response)['errors']
      var msg = '<p>Could not delete the script because of the following errors:</p><ul>'
      $.each(errors, function (index, value) {
        msg += '<li>' + value + '</li>'
      })
      msg += '</ul>'
    } else {
      bootbox.alert('<p>The script was deleted.</p>')
    }
  })
  .fail(function (jqXHR, textStatus, errorThrown) {
    bootbox.alert({
      message: '<p>The script could not be updated because of the following errors:</p>'+response,
      callback: function () {
        return 'Error: ' + textStatus + ': ' + errorThrown
      }
    })
  })
}


// General Export Function
function exportScript() {
  // Get the manifest, query, and action
    var manifest = validateQuery(['name']) // Returns form vals or false
    if (manifest !== false) {
      var data = {'action': 'export', 'query': manifest['db-query'], 'manifest': manifest}
      data = JSON.stringify(data)
      $.ajax({
        method: 'POST',
        url: '/scripts/export-script',
        data: data,
        contentType: 'application/json;charset=UTF-8'
      })
      .done(function (response) {
        if (JSON.parse(response)['result'] == 'fail') {
          var errors = JSON.parse(response)['errors']
          var msg = '<p>Could not save the script because of the following errors:</p><ul>'
          $.each(errors, function (index, value) {
            msg += '<li>' + value + '</li>'
          })
          msg += '</ul>'
        } else {
          window.location = '/scripts/download-export/' + manifest['name'] + '.zip'
        }
        bootbox.alert({
          message: msg
        })
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>The script could not be updated because of the following errors:</p>'+response,
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
    'data': formvals
  }
  console.log('Sending')
  $.ajax({
    method: 'POST',
    url: '/scripts/launch-jupyter',
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
  $('#go').click(function(e){
    var name = $('#display').val();
    window.location = '/scripts/display/' + name; 
  });
  $('#display').on('keypress',function(e){
   var key = (e.keyCode || e.which);
      if(key == 13 || key == 3){
         $('#go').click();
      }
  });

  // Preview Show and Hide Buttons
  $('#preview').click(function (e) {
    e.preventDefault()
    $('form').hide()
    $('#previewDisplay').show()
    var jsonform = cleanup()
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
    saveScript($(this).attr('data-action'))
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
            deleteScript(name)
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
    exportScript()
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
