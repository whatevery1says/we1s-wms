//
// General Helper Functions
//

function jsonifyForm (formObj) {
  /* Handles JSON form serialisation */
  var form = {}
  $.each(formObj.serializeArray(), function (i, field) {
    form[field.name] = field.value || ''
  })
  return form
}

//
// Ajax Functions
//

function createManifest (jsonform) {
  /* Creates a new manifest
  Input: A JSON serialisation of the form values
  Returns: A copy of the manifest and an array of errors for display */
  var manifest = JSON.stringify(jsonform, null, '  ')
  $.ajax({
    method: 'POST',
    url: '/corpus/create-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var manifest = JSON.parse(response)['manifest']
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        var msg = '<p>Could not save the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>Saved the following manifest:</p>' + manifest
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          // window.location = '/corpus'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      var msg = '<p>The manifest could not be saved because of the following errors:</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function deleteManifest (name, metapath) {
  /* Deletes a manifest
   Input: A name value
   Returns: An array of errors for display */
  $.ajax({
    method: 'POST',
    url: '/corpus/delete-manifest',
    data: JSON.stringify({'name': name, 'metapath': metapath}),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        var msg = '<p>Could not delete the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>The manifest for <code>' + name + '</code> was deleted.</p>'
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/corpus'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      var msg = '<p>The manifest could not be saved because of the following errors:</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function exportSearch (data) {
  /* Exports the results of a Corpus search
     Input: Values from the search form
     Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/corpus/export-search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      response = JSON.parse(response)
      if (response['errors'].length !== 0) {
        var result = JSON.stringify(response['errors'])
        bootbox.alert('<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>')
      } else {
        window.location = '/corpus/download-export/' + response['filename']
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function searchCorpus (data) {
  /* Searches the Corpus
     Input: Values from the search form
     Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/corpus/search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      $('#results').empty()
      hideProcessing()
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
          var link = '/corpus/display/' + item['name']
          out += '<h4><a href="' + link + '">' + item['name'] + '</a></h4><br>'
          $.each(item, function (key, value) {
            value = JSON.stringify(value)
            if (key === 'content' && value.length > 200) {
              value = value.substring(0,200) + '...'
            }
            out += '<code>' + key + '</code>: ' + value + '<br>'
          })
          out += '<hr>'
        })
        var $pagination = $('#pagination')
        var defaultOpts = {
          visiblePages: 5,
          initiateStartPageClick: false,
          onPageClick: function (event, page) {
            var newdata = {
              'query': $('#query').val(),
              'regex': $('#regex').is(':checked'),
              'limit': $('#limit').val(),
              'properties': $('#properties').val(),
              'page': page
            }
            searchCorpus(newdata)
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
      hideProcessing()
      var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function sendExport (jsonform) {
  /* Sends the export options to the server
     Input: A serialised set of form values from the export modal
     Returns: The name of the file to download.
     Automatically redirects to the download function. */
  $.ajax({
    method: 'POST',
    url: '/corpus/send-export',
    data: JSON.stringify(jsonform),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var filename = JSON.parse(response)['filename']
      // $('.modal-body').html(filename)
      $('#exportModal').modal('hide')
      // bootbox.alert({
      //   message: filename
      // })
      window.location = '/corpus/download-export/' + filename
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function updateManifest (jsonform, name) {
  /* Updates the displayed manifest
     Input: A JSON serialisation of the form values
     Returns: A copy of the manifest and an array of errors for display */
  var manifest = JSON.stringify(jsonform, null, '  ')
  $.ajax({
    method: 'POST',
    url: '/corpus/update-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      var manifest = JSON.parse(response)['manifest']
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        var msg = '<p>Could not update the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>Updated the following manifest:</p>' + manifest
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/corpus'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
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
  const form = jsonifyForm($('#manifestForm'))
  const newform = {}
  const exclude = ['licenseName', 'licensePath', 'licenseTitle',
                   'sourceEmail', 'sourcePath', 'sourceTitle',
                   'contributorTitle', 'contributorOrg', 'contributorGroup', 
                   'contributorPath', 'contributorEmail', 'contributorRole', 'notesField']
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
  const csvs2 = ['queryterms']
  for (const property of csvs2) {
    // Only process defined properties
    if (typeof newform[property] !== 'undefined') {
      newform[property] = newform[property].trim().split(/\s*,\s*/)
    }
  }
    const csvs3 = ['processes']
  for (const property of csvs3) {
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
  const objects2 = ['contributors']
  for (var property of objects2) {
    newform[property] = eval(newform[property])
    // Only process defined properties
    if (typeof newform[property] !== 'undefined') {
      // Convert evil properties from hidden fields to a list
      let gD = {}
      let gL = []
      let eP = []
      // Get the property keys
      $.each(newform[property], function (key, value) {
        $.each(value, function (k, v) {
          eP.push(k)
        })
      })
      // Build object for each ID
      $.each(eP, function (key, item) {
        item = item.replace(/[a-zA-Z]+/, '')
        gD[item] = {}
      })
      // Add the values to the good dict by ID
      $.each(newform[property], function (i, item) {
        let obj = newform[property][i]
        let k = Object.keys(obj)
        let prop = k[0]
        let id = prop.replace(/[a-zA-Z]+/, '')
        let val = item[prop]
        if (prop.startsWith('contributorTitle')) {
          prop = 'title'
          gD[id][prop] = val
        }
        if (prop.startsWith('contributorGroup')) {
          prop = 'group'
          gD[id][prop] = val
        }
        if (prop.startsWith('contributorOrg')) {
          prop = 'organization'
          gD[id][prop] = val
        }
        if (prop.startsWith('contributorPath')) {
          prop = 'path'
          gD[id][prop] = val
        }
        if (prop.startsWith('contributorEmail')) {
          prop = 'email'
          gD[id][prop] = val
        }
        if (prop.startsWith('contributorRole')) {
          prop = 'role'
          gD[id][prop] = val
        }
      })
      // Convert any contributor names to strings and add the good_dict values to the list
      $.each(gD, function (k, v) {
        if (gD[k].length === 1) {
          v = gD[k]['title']
        } else {
          gL.push(v)
        }
      })
      newform[property] = gL
    }
  }
  const objects3 = ['sources']
  for (var property of objects3) {
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
        if (prop.startsWith('sourceEmail')) {
          prop = 'email'
          goodDict[id][prop] = val
        }
        if (prop.startsWith('sourceTitle')) {
          prop = 'title'
          goodDict[id][prop] = val
        }
        if (prop.startsWith('sourcePath')) {
          prop = 'path'
          goodDict[id][prop] = val
        }
      })
      // Convert any source emails to strings and add the good_dict values to the list
      $.each(goodDict, function (k, v) {
        if (goodDict[k].length === 1) {
          v = goodDict[k]['email']
        } else {
          goodList.push(v)
        }
      })
      newform[property] = goodList
    }
  }
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

  $(document).on('click', '.add-source', function () {
    // Keep count of the number of fields in session storage
    if ('sourceCount' in sessionStorage) {
      var count = parseInt(sessionStorage.getItem('sourceCount')) + 1
      sessionStorage.setItem('sourceCount', count.toString())
    } else {
      count = 0
      sessionStorage.setItem('sourceCount', '0')
    }
    // Show the remove icon
    $(this).next().removeClass('hidden')
    // Clone the template
    var $template = $('#sources-template').clone()
    $(this).closest('.row').after($template.html())
    $('.sourceEmail').last().attr('id', 'sourceEmail' + count).removeClass('.sourceEmail')
    $('.sourcePath').last().attr('id', 'sourcePath' + count).removeClass('.sourcePath')
    $('.sourceTitle').last().attr('id', 'sourceTitle' + count).removeClass('.sourceTitle')
    // Serialise the textareas and save the string to the hidden sources field
    var serialisedTextareas = serialiseTextareas('.source-field')
    $('#sources').val(serialisedTextareas)
    // console.log($('#sources').val())
  })

  $(document).on('click', '.remove-source', function () {
    // If the field to remove is the only one, clone a new one
    // NB. There are three sub-fields
    if ($('.source-field').length === 3) {
      var count = parseInt(sessionStorage.getItem('sourceCount')) + 1
      sessionStorage.setItem('sourceCount', count.toString())
      var $template = $('#sources-template').clone()
      $(this).closest('.row').after($template.html())
      $('.sourceEmail').last().attr('id', 'sourceEmail' + count).removeClass('.sourceEmail')
      $('.sourcePath').last().attr('id', 'sourcePath' + count).removeClass('.sourcePath')
      $('.sourceTitle').last().attr('id', 'sourceTitle' + count).removeClass('.sourceTitle')
    }
    // Remove the source field
    $(this).parent().parent().remove()
    // Display the "sources" label
    $('.source-field').eq(0).parent().prev().text('sources')
    // Serialise the textareas and save the string to the hidden sources field
    var serialisedTextareas = serialiseTextareas('.source-field')
    $('#sources').val(serialisedTextareas)
    // console.log($('#sources').val())
  })
  //can probably give all
  $(document).on('blur', '.source-field', function () {
    // Re-serialise the text areas when the user clicks on another element
    var serialisedTextareas = serialiseTextareas('.source-field')
    $('#sources').val(serialisedTextareas)
    // console.log($('#sources').val())
  })

// contributors start

  $(document).on('click', '.add-contributor', function () {
    // Keep count of the number of fields in session storage
    if ('contributorCount' in sessionStorage) {
      var count = parseInt(sessionStorage.getItem('contributorCount')) + 1
      sessionStorage.setItem('contributorCount', count.toString())
    } else {
      count = 0
      sessionStorage.setItem('contributorCount', '0')
    }
    // Show the remove icon
    $(this).next().removeClass('hidden')
    // Clone the template
    var $template = $('#contributors-template').clone()
    $(this).closest('.row').after($template.html())
    $('.contributorTitle').last().attr('id', 'contributorTitle' + count).removeClass('.contributorTitle')
    $('.contributorGroup').last().attr('id', 'contributorGroup' + count).removeClass('.contributorGroup')
    $('.contributorOrg').last().attr('id', 'contributorOrg' + count).removeClass('.contributorOrg')
    $('.contributorPath').last().attr('id', 'contributorPath' + count).removeClass('.contributorPath')
    $('.contributorEmail').last().attr('id', 'contributorEmail' + count).removeClass('.contributorEmail')
    $('.contributorRole').last().attr('id', 'contributorRole' + count).removeClass('.contributorRole')
    // Serialise the textareas and save the string to the hidden contributors field
    var serialisedTextareas = serialiseTextareas('.contributor-field')
    $('#contributors').val(serialisedTextareas)
    // console.log($('#contributors').val())
  })

  $(document).on('click', '.remove-contributor', function () {
    // If the field to remove is the only one, clone a new one
    // NB. There are three sub-fields
    if ($('.contributor-field').length === 6) {
      var count = parseInt(sessionStorage.getItem('contributorCount')) + 1
      sessionStorage.setItem('contributorCount', count.toString())
      var $template = $('#contributors-template').clone()
      $(this).closest('.row').after($template.html())
      $('.contributorTitle').last().attr('id', 'contributorTitle' + count).removeClass('.contributorTitle')
      $('.contributorGroup').last().attr('id', 'contributorGroup' + count).removeClass('.contributorGroup')
      $('.contributorOrg').last().attr('id', 'contributorOrg' + count).removeClass('.contributorOrg')
      $('.contributorPath').last().attr('id', 'contributorPath' + count).removeClass('.contributorPath')
      $('.contributorEmail').last().attr('id', 'contributorEmail' + count).removeClass('.contributorEmail')
      $('.contributorRole').last().attr('id', 'contributorRole' + count).removeClass('.contributorRole')
    }
    // Remove the contributor field
    $(this).parent().parent().remove()
    // Display the "contributors" label
    $('.contributor-field').eq(0).parent().prev().text('contributors')
    // Serialise the textareas and save the string to the hidden contributors field
    var serialisedTextareas = serialiseTextareas('.contributor-field')
    $('#contributors').val(serialisedTextareas)
    // console.log($('#contributors').val())
  })

  $(document).on('blur', '.contributor-field', function () {
    // Re-serialise the text areas when the user clicks on another element
    var serialisedTextareas = serialiseTextareas('.contributor-field')
    $('#contributors').val(serialisedTextareas)
    // console.log($('#contributors').val())
  })
  // End Property Cloning
// contributors end


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
// $(document).ready() Event Handling
//

$(document).ready(function () {
  //
  // Index Page Functions
  //

  /* Handles the Display form on the index page */
  $('#go').click(function (e) {
    var name = $('#display').val()
    window.location = '/corpus/display/' + name
  })
  $('#display').on('keypress', function (e) {
    var key = (e.keyCode || e.which)
    if (key === 13 || key === 3) {
      $('#go').click()
    }
  })

  //
  // Create and Display Page Functions
  //

  /* Handles the manifest preview and hide buttons */
  $('#preview').click(function (e) {
    e.preventDefault()
    $('form').hide()
    $('#previewDisplay').show()
    var jsonform =  cleanup()
    $('#manifest').html(JSON.stringify(jsonform, null, '  '))
  })

  $('#hide').click(function (e) {
    e.preventDefault()
    $('#previewDisplay').hide()
    $('form').show()
  })

  $('#save').click(function (e) {
    e.preventDefault()
    $('#manifestForm').submit()
  })

  //
  // Create Page Functions
  //

  /* Handles form submission for record creation */
  $($('#manifestForm')).on('submit', function (e) {
    e.preventDefault()
    if ($(this).parsley().isValid()) {
      var jsonform = jsonifyForm($('#manifestForm'))
      createManifest(jsonform)
    }
  })

  /* Handles the nodetype buttons for creating manifests */
  $('input[name="nodetype"]').click(function (e) {
    var val = $(this).val()
    var setting = val.toLowerCase()
    switch (true) {
      case setting === 'collection' || setting === 'rawdata' || setting === 'processeddata':
        var template = $('#' + setting + '-template').html()
        $('#manifestCard').html(template)
        break
      case setting === 'branch':
        template = $('#branch-template').html()
        $('#manifestCard').html(template)
        break
      default:
        template = $('#generic-template').html()
        $('#manifestCard').html(template)
        $('#name').val(val)
        $('#title').val(val)
    }
    $('.nav-tabs a[href="#required"]').tab('show')
  })

  //
  // Display Page Functions
  //

  /* Makes the global template available to scripts for the display page */
  var globalTemplate = $('#global-template').html()

  /* If this is the display page, use the correct form for the 
     manifest's nodetype */
  var pageUrl = document.URL.split('/')
  if (pageUrl[pageUrl.length - 2] === 'display') {
    var template = $('#' + nodetype + '-template').html()
    $('#manifestCard').html(template).append(globalTemplate)
  }

  /* Toggles the Edit/Update button and field disabled property */
  $('#update').click(function (e) {
    e.preventDefault()
    if ($('#update').html() === 'Edit') {
      $('form').find('input, textarea, select').each(function () {
        if ($(this).attr('id') !== 'name' && $(this).attr('id') !== 'manifest-content') {
          $(this).prop('readonly', false)
          $(this).removeClass('disabled')
        }
        if ($(this).attr('id') === 'path' && nodetype === 'collection') {
          $(this).prop('readonly', true)
          $(this).addClass('disabled')
        }
      })
      $('#update').html('Update')
    } else {
      var name = $('#name').val()
      bootbox.confirm({
        message: 'Are you sure you wish to update the record for <code>' + name + '</code>?',
        buttons: {
          confirm: {label: 'Yes', className: 'btn-success'},
          cancel: {label: 'No', className: 'btn-danger'}
        },
        callback: function (result) {
          if (result === true) {
            var name = $('#name').val()
            var path = $('#path').val()
            var jsonform =  jsonifyForm($('#manifestForm'))
            $.extend(jsonform, {'name': name})
            $.extend(jsonform, {'path': path})
            updateManifest(jsonform, name)
          }
        }
      })
    }
  })

  /* Handles the Delete button */
  $('#delete').click(function (e) {
    e.preventDefault()
    var name = $('#name').val()
    var metapath = $('#metapath').val()
    bootbox.confirm({
      message: 'Are you sure you wish to delete <code>' + name + '</code>?',
      buttons: {
        confirm: {label: 'Yes', className: 'btn-success'},
        cancel: {label: 'No', className: 'btn-danger'}
      },
      callback: function (result) {
        if (result === true) {
          deleteManifest(name, metapath)
        }
      }
    })
  })

  /* Handles the Export feature */
  $('#export').click(function (e) {
    e.preventDefault()
    $('#exportModal').modal()
  })

  /* Handles behaviour when Select All is changed */
  $('#selectall').change(function (e) {
    if ($(this).is(':checked')) {
      $('.exportchoice').prop('checked', true)
      $('#manifestonly').prop('checked', false)
    } else {
      $('.exportchoice').prop('checked', false)
    }
  })

  /* Handles behaviour when Manifest Only is changed */
  $('#manifestonly').change(function (e) {
    if ($(this).is(':checked')) {
      $('.exportchoice').prop('checked', false)
      $('#selectall').prop('checked', false)
    }
    $(this).prop('checked', true)
  })

  /* Serialises the export options and initiates the export */
  $('#doExport').click(function (e) {
    // Get an array of export options
    var opts = {'exportoptions': []}
    $('.exportchoice:checked').each(function () {
      opts['exportoptions'].push(this.value)
    })
    var jsonform = jsonifyForm($('#manifestForm'))
    $.extend(jsonform, opts)
    sendExport(jsonform)
  })

  //
  // Import Page Functions
  //

  /* Change the metadata form in import */
  $('#category').change(function () {
    var selected = $(this).val().toLowerCase()
    if (selected === 'rawdata' || selected === 'processeddata') {
      template = $('#' + selected + '-template').html()
    } else {
      template = $('#generic-template').html()
    }
    $('#metadataCard').html(template).append(globalTemplate)
  })

  /* Change the Show/Hide Metadata Button */
  $('#collapseOne').on('shown.bs.collapse', function () {
    $('#showMetadata').text('Hide Metadata')
  })
  $('#collapseOne').on('hidden.bs.collapse', function () {
    $('#showMetadata').text('Show Metadata')
  })

  //
  // Search Page Functions
  //

  /* Handles the Search feature */
  $('#searchCorpus').click(function (e) {
    e.preventDefault()
    var data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': 1
    }
    searchCorpus(data)
  })

  /* Handles the Search Export feature */
  /*
  $('#exportSearchResults').click(function (e) {
    e.preventDefault()
    var data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': 1,
      'paginated': false
    }
    var querystring = JSON.stringify($('#builder').queryBuilder('getMongo'), undefined, 2)
    var advancedOptions = JSON.stringify(serialiseAdvancedOptions (), undefined, 2)
    data = {
      'query': JSON.parse(querystring),
      'advancedOptions': JSON.parse(advancedOptions),
      'paginated': false
    }
    alert(JSON.stringify(data))
    exportSearch(data)
  }) */

  /* Toggles the search form */
  $('#hideSearch').click(function () {
    if ($('#hideSearch').html() === 'Hide Form') {
      $('#search-form').hide()
      $('#exportSearchResults').show()
      $('#results').show()
      $('#pagination').show()	
      $('#hideSearch').html('Show Form')
    } else {
      $('#hideSearch').html('Hide Form')
      $('#exportSearchResults').hide()
      $('#results').hide()
      $('#pagination').hide()
      $('#search-form').show()
    }
  })

  /* Handles the pagination buttons */
  $('.page-link').click(function (e) {
    e.preventDefault()
    var data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': $(this).html()
    }
    searchCorpus(data)
  })

  /* Handles server imports */
  $(document).on('click', '.server-import', function (e) {
    e.preventDefault()
    var data = {}
    data['collection'] = $('#collection').val()
    data['category'] = $('#category').val()
    data['branch'] = $('#branch').val()
    data['filename'] = $(this).attr('data-server')
    var btn = $(this)
    $.ajax({
      method: 'POST',
      url: '/corpus/import-server-file',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8',
      beforeSend: showProcessing()
    })
      .done(function (response) {
        hideProcessing()
        var errors = JSON.parse(response)['errors']
        if (errors.length > 0) {
          btn.replaceWith('<i class="fa fa-2x fa-times text-danger"></i>')
          var msg = '<p>Could not update the manifest because of the following errors:</p><ul>'
          $.each(errors, function (index, value) {
            msg += '<li>' + value + '</li>'
          })
          msg += '</ul>'
        } else {
          msg = '<p>The import was successful.</p>'
          btn.replaceWith('<i class="fa fa-2x fa-check text-success"></i>')
        }
        bootbox.alert(msg)
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        hideProcessing()
        var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
        msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
        bootbox.alert(msg)
      })
  })

  /* Refreshes the server import view */
  $('#refresh').click(function (e) {
    e.preventDefault()
    console.log('refreshing data')
    var data = {}
    $.ajax({
      method: 'POST',
      url: '/corpus/refresh-server-imports',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8',
      beforeSend: showProcessing()
    })
      .done(function (response) {
        console.log('refreshing table')
        response = JSON.parse(response)
        $('#server-import-previews').empty()
        $.each(response['file_list'], function (index, value) {
          var row = '<div id="server-import-template" class="file-row">'
          row += '<div><span class="preview">' + value + '<img data-dz-thumbnail /></span></div>'
          row += '<div><p class="name" data-dz-name></p><strong class="error text-danger" data-dz-errormessage></strong></div>'
          row += '<div><p class="size" data-dz-size></p>'
          row += '<div class="progress progress-striped active import-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">'
          row += '<div class="progress-bar progress-bar-success" style="width:0%;" data-dz-uploadprogress></div>'
          row += '</div></div><div>'
          row += '<button class="btn btn-outline-editorial server-import" data-server="' + value + '"><i class="fa fa-upload"></i><span>Import</span></button>'
          row += '</div></div>'
          $('#server-import-previews').append(row)
        })
        console.log('table refreshed')
        hideProcessing()
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        hideProcessing()
        var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
        msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
        bootbox.alert(msg)
      })
  })
}) /* End of $(document).ready() Event Handling */
