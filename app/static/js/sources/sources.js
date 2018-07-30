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
    url: '/sources/create-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var manifest = JSON.parse(response)['manifest']
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        bootbox.alert('<p>Could not save the manifest because of the following errors:</p>' + errors)
      } else {
        var msg = '<p>Saved the following manifest:</p>' + manifest
        bootbox.alert({
          message: msg,
          callback: function () {
            window.location = '/sources'
          }
        })
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>' + response,
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function deleteManifest (name, metapath) {
  /* Deletes a manifest
     Input: A name value
     Returns: An array of errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/delete-manifest',
    data: JSON.stringify({'name': name, 'metapath': metapath}),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        var msg = '<p>Could not delete the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>The manifest for <code>' + name + '</code> was deleted.</p>'
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>' + response,
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function exportSourceManifest () {
  /* Exports a single source manifest from the Display page.
     Input: Values from the search form
     Returns: An array containing results and errors for display */

  var filename = $('#name').val() + '.json'
  $.ajax({
    method: 'POST',
    url: '/sources/export-manifest',
    data: JSON.stringify({'name': $('#name').val()}),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
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
        window.location = '/sources/download-export/' + filename
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

function exportSearch (data) {
  /* Exports the results of a Sources search
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
        var result = JSON.stringify(response['errors'])
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>',
          callback: function () {
            ('Error: ' + textStatus + ': ' + errorThrown)
          }
        })
      } else {
        window.location = '/sources/download-export/' + response['filename']
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

function searchSources (data) {
  /* Searches the Sources database
    Input: Values from the search form
    Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      $('#results').empty()
      response = JSON.parse(response)
      if (response['errors'].length !== 0) {
        var result = response['errors']
      } else {
        result = response['response']
      }
      // Make the result into a string
      var out = ''
      $.each(result, function (i, item) {
        var link = '/sources/display/' + item['name']
        out += '<h4><a href="' + link + '">' + item['name'] + '</a></h4><br>'
        $.each(item, function (key, value) {
          value = JSON.stringify(value)
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
          searchSources(newdata)
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

function updateManifest (jsonform, name) {
  /* Updates the displayed manifest
     Input: A JSON serialisation of the form values
     Returns: A copy of the manifest and an array of errors for display */
  var manifest = JSON.stringify(jsonform, null, '  ')
  $.ajax({
    method: 'POST',
    url: '/sources/update-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8'
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
          window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be updated because of the following errors:</p>' + response,
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function cleanup () {
  const form = jsonifyForm()
  const newform = {}
  const exclude = ['authorName', 'authorOrg', 'authorGroup', 'notesField']
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
  const objects = ['authors']
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
        if (prop.startsWith('authorName')) {
          prop = 'name'
          goodDict[id][prop] = val
        }
        if (prop.startsWith('authorGroup')) {
          prop = 'group'
          goodDict[id][prop] = val
        }
        if (prop.startsWith('authorOrg')) {
          prop = 'organization'
          goodDict[id][prop] = val
        }
      })
      // Convert any author names to strings and add the good_dict values to the list
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

//
// $(document).ready() Event Handling
//

$(document).ready(function () {
  //
  // Index Page Functions
  //

  /* Handles the Display form */
  $('#go').click(function (e) {
    var name = $('#display').val()
    window.location = '/sources/display/' + name
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
    var jsonform = cleanup() // jsonifyForm()
    $('#manifest').html(JSON.stringify(jsonform, null, '  '))
  })

  $('#hide').click(function (e) {
    e.preventDefault()
    $('#previewDisplay').hide()
    $('form').show()
  })

  //
  // Create Page Functions
  //

  /* Handles form submission for record creation */
  $('form').on('submit', function (e) {
    e.preventDefault()
    if ($(this).parsley().isValid()) {
      var jsonform = jsonifyForm()
      var exclude = ['authorName', 'authorOrg', 'authorGroup', 'notesField']
      for (var property of exclude) {
        delete jsonform[property]
      }
      $.each(jsonform, function (k, v) {
        if (v.length === 0) {
          delete jsonform[k]
        }
      })
      createManifest(jsonform)
    }
  })

  // Handle Property Cloning
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

  $(document).on('click', '.add-author', function () {
    // Keep count of the number of fields in session storage
    if ('authorCount' in sessionStorage) {
      var count = parseInt(sessionStorage.getItem('authorCount')) + 1
      sessionStorage.setItem('authorCount', count.toString())
    } else {
      count = 0
      sessionStorage.setItem('authorCount', '0')
    }
    // Show the remove icon
    $(this).next().removeClass('hidden')
    // Clone the template
    var $template = $('#authors-template').clone()
    $(this).closest('.row').after($template.html())
    $('.authorName').last().attr('id', 'authorName' + count).removeClass('.authorName')
    $('.authorGroup').last().attr('id', 'authorGroup' + count).removeClass('.authorGroup')
    $('.authorOrg').last().attr('id', 'authorOrg' + count).removeClass('.authorOrg')
    // Serialise the textareas and save the string to the hidden authors field
    var serialisedTextareas = serialiseTextareas('.author-field')
    $('#authors').val(serialisedTextareas)
    // console.log($('#authors').val())
  })

  $(document).on('click', '.remove-author', function () {
    // If the field to remove is the only one, clone a new one
    // NB. There are three sub-fields
    if ($('.author-field').length === 3) {
      var count = parseInt(sessionStorage.getItem('authorCount')) + 1
      sessionStorage.setItem('authorCount', count.toString())
      var $template = $('#authors-template').clone()
      $(this).closest('.row').after($template.html())
      $('.authorName').last().attr('id', 'authorName' + count).removeClass('.authorName')
      $('.authorGroup').last().attr('id', 'authorGroup' + count).removeClass('.authorGroup')
      $('.authorOrg').last().attr('id', 'authorOrg' + count).removeClass('.authorOrg')
    }
    // Remove the author field
    $(this).parent().parent().remove()
    // Display the "authors" label
    $('.author-field').eq(0).parent().prev().text('authors')
    // Serialise the textareas and save the string to the hidden authors field
    var serialisedTextareas = serialiseTextareas('.author-field')
    $('#authors').val(serialisedTextareas)
    // console.log($('#authors').val())
  })

  $(document).on('blur', '.author-field', function () {
    // Re-serialise the text areas when the user clicks on another element
    var serialisedTextareas = serialiseTextareas('.author-field')
    $('#authors').val(serialisedTextareas)
    // console.log($('#authors').val())
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

  // Initialize the datepicker
  //   $('#date').dateformat()

  //
  // Display Page Functions
  //

  /* Toggles the Edit/Update button and field disabled property */
  $('#update').click(function (e) {
    e.preventDefault()
    if ($('#update').html() === 'Edit') {
      $('form').find('input, textarea, select').each(function () {
        if ($(this).attr('id') !== 'name') {
          $(this).prop('readonly', false)
          $(this).removeClass('disabled')
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
            name = $('#name').val()
            var jsonform = jsonifyForm()
            $.extend(jsonform, {'name': name})
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
    exportSourceManifest()
  })

  //
  // Search Page Functions
  //

  /* Handles the Search feature */
  $('#searchSources').click(function (e) {
    e.preventDefault()
    var data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': 1
    }
    searchSources(data)
  })

  /* Handles the Search Export feature */
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
    exportSearch(data)
  })

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
    searchSources(data)
  })
}) /* End of $(document).ready() Event Handling */
