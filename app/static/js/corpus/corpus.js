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
    var jsonform =  jsonifyForm($('#manifestForm'))
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
