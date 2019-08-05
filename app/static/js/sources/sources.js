/* global bootbox, exportSearch, hideProcessing, moment, searchSources, showProcessing */
/* eslint no-undef: "error" */
//
// General Helper Functions
//

  // Deprecated - Validate a single date for use when a single datepicker is closed
  function checkDateFormat (date) {
    // If the field is not empty
    let valid
    if (date !== '' && date !== null) {
      if (moment(date, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
        valid = true
      } else {
        valid = false
      }
    }
    return valid
  }

function cleanup () {
  /* Serialises the form values and converts strings in hidden fields and 
  session storage to proper JSON format. */
  // Serialise fields, including disabled ones
  const formvals = {}
  $('#manifestForm input, textarea, select').each(function () {
    let name = $(this).prop('name')
    let val = $(this).val() || ''
    formvals[name] = val
  })
  $('.datepicker').each(function () {
    let name = $(this).prop('name')
    let val = $(this).val() || ''
    formvals[name] = val
  })
  const newform = {}
  const clones = ['authors', 'notes']
  let prefixes = {
    'authors': 'author'
  }
  const csvs = ['keywords']
  const checkboxes = []
  const lists = ['authors', 'notes']
  const exclude = [
    'authorName', 'authorOrg', 'authorGroup', 'notesField'
  ]
  // Copy the form values, ommitting empty fields and exclusions
  $.each(formvals, function (key, value) {
    if (value !== '' && value !== [] && $.inArray(key, exclude) === -1) {
      // Reformat cloneable fields
      if ($.inArray(key, clones) !== -1) {
        value = clones2Lists(value, key, prefixes, lists)
      }
      newform[key] = value
    }
  })
  // Convert comma-separated values to arrays
  for (const property of csvs) {
    // Only process defined properties
    if (typeof newform[property] !== 'undefined') {
      newform[property] = newform[property].trim().split(/\s*,\s*/)
    }
  }
  // Convert check boxes to Boolean values
  for (const property of checkboxes) {
    if (newform[property] === 'on') {
      newform[property] = true
    } else {
      delete newform[property]
    }
  }
  // Handle citations
  try {
    newform['citation'] = JSON.parse(formvals['citation'][0])
  } catch (err) {
    newform['citation'] = formvals['citation'][0]
  }
  // Handle dates
  let result = processDates()
  if (result['errors'].length !== 0) {
    var msg = '<p>Please correct the following errors</p><ul>'
    $.each(result['errors'], function (_, value) {
      msg += '<li>' + value + '</li>'
    })
    msg += '</ul>'
    bootbox.alert(msg)
  }
  if (result['dates'].hasOwnProperty('created') && result['dates']['created'] !== null && result['dates']['created'].length > 0) {
    newform['created'] = result['dates']['created']
  } else {
    delete newform['created']
  }
  if (result['dates'].hasOwnProperty('updated') && result['dates']['updated'] !== null && result['dates']['updated'].length > 0) {
    newform['updated'] = result['dates']['updated']
  } else {
    delete newform['updated']
  }
  return newform
  /* Needs to be logic here to return errors so that the save function can be invoked only
     if there are no errors. */
}

function clones2Lists (str, prefix, prefixes, lists) {
  // Takes a string of cloned (or cloneable) fields and converts it to a schema-valid object.
  // The prefix is something like 'source', which appears in 'sourceTitle, sourcePath', etc.
  let propertyArray = []
  let clonedObj = []
  let obj = JSON.parse(str)
  $.each(obj, function (key, value) {
    let prop = Object.keys(value)[0].replace(/\d+/, '').replace(prefixes[prefix], '').toLowerCase()
    let id = Object.keys(value)[0].replace(/\D+/, '').toString()
    let val = value[Object.keys(value)[0]]
    // Serialise as simple array
    if ($.inArray(prefix, lists) !== -1) {
      propertyArray.push(val)
    // Serialise as an array of objects
    } else {
      // Add id to clonedObj
      if (!(id in clonedObj)) {
        let d = {}
        d[prop] = val
        clonedObj.push({'id': id, 'properties': d})
      // Add new property to pre-existing id
      } else {
        clonedObj[id]['properties'][prop] = val
      }
    }
    // console.log('clonedObj ' + key)
    // console.log(clonedObj)
  })
  // This might be problematic for notes.
  $.each(clonedObj, function (_, value) {
    propertyArray.push(value['properties'])
  })
  return propertyArray
}

function processDates () {
  let dates = []
  let errors = []
  $('.daterange').each(function () {
    // Validate all dates
    let property = $(this).find('button').first().data('row')
    let startDateField = $(this).find('input').eq(0)
    let endDateField = $(this).find('input').eq(1)
    let result = validateDates(startDateField, endDateField, property)
    errors = errors.concat(result)
  })
  // If the dates are valid, serialise them
  if (errors.length === 0) {
    dates = serialiseDates()
  }
  return {'dates': dates, 'errors': errors}
}

// Validate a date range row
function validateDates (startField, endField, property) {
  let errors = []
  let start = startField.val()
  let end = endField.val()
  let numRows = $('.' + property + '-row').length
  switch (true) {
    case start.length === 0 && end.length === 0 && numRows > 1:
      errors.push('Please delete the empty date row for the ' + property + ' property.')
      break
    case start.length > 0 && end.length === 0:
      if (!moment(start, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
        errors.push('A start field in the ' + property + ' property contains an invalid date type. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
      }
      break
    case start.length === 0 && end.length > 0:
      errors.push('Please enter a date in the empty ' + property + ' start field . Dates that are not date ranges should be entered in the start field, and the end field should be left empty.')
      break
    default:
      if (!moment(start, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
        if (numRows !== 1) {
          errors.push('A start field in the ' + property + ' property contains an invalid date type. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
        }
      }
      if (!moment(end, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
        if (numRows !== 1 && end.length !== 0) {
          errors.push('An end field in the ' + property + ' property contains an invalid date type. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
        }
      }
  }
  // Make sure the start date precedes the end date
  if (end.length > 0 && !moment(start).isBefore(moment(end))) {
    errors.push('The ' + property + ' property contains an end date earlier than the start date in the same row.')
  }
  return errors
}

// Serialise all dates for insertion in the manifest
function serialiseDates () {
  let dates = {
    'created': [],
    'updated': []
  }
  $('.daterange').each(function () {
    var date
    let fieldType = $(this).find('button').first().data('row')
    let startDate = $(this).find('input').eq(0).val()
    let endDate = $(this).find('input').eq(1).val()
    // Format the date values from the input field
    if (startDate.length > 0) {
      if (moment(startDate, 'YYYY-MM-DDTHH:mm:ss', true).isValid()) {
        startDate = moment(startDate).toISOString()
      } else {
        startDate = moment(startDate).format('YYYY-MM-DD')
      }
    }
    if (endDate.length > 0) {
      if (moment(endDate, 'YYYY-MM-DDTHH:mm:ss', true).isValid()) {
        endDate = moment(endDate).toISOString()
      } else {
        endDate = moment(endDate).format('YYYY-MM-DD')
      }
    }
    // Set the date value to pass to the serialiser
    if (startDate === '' || startDate === null) {
      date = null
    } else if (endDate === '' || endDate === null) {
      date = startDate
    } else {
      date = {
        'start': startDate,
        'end': endDate
      }
    }
    // Push the date to the dates object to pass to the serialsier
    if (date !== null) {
      dates[fieldType].push(date)
    }
    // Delete empty properties from the dates object
    if (dates[fieldType][0] === null) {
      delete dates[fieldType]
    }
  })
  return dates
}

function uniqueId () {
  /* Return a unique ID */
  return Math.random().toString(36).substring(2) + (new Date()).getTime().toString(36)
}

//
// Ajax Functions
//

function deleteManifest (name, metapath) {
  /* Deletes a manifest
     Input: A name value
     Returns: An array of errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/delete-manifest',
    data: JSON.stringify({ 'name': name, 'metapath': metapath }),
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
          window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>' + response,
        callback: function () {
          return 'Error: ' + textStatus + ': ' + errorThrown
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
    data: JSON.stringify({ 'name': $('#name').val() }),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      response = JSON.parse(response)
      if (response['errors'].length !== 0) {
        var result = JSON.stringify(response['errors'])
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>'
        })
      } else {
        window.location = '/sources/download-export/' + filename
      }
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

function exportSearch (data) {
  /* Exports the results of a Sources search
     Input: Values from the search form
     Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/export-search',
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
          message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>'
        })
      } else {
        window.location = '/sources/download-export/' + response['filename']
      }
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

function saveManifest (data, action) {
  /* Creates a new manifest
  Input: A JSON serialisation of the form values
  Returns: A copy of the manifest and an array of errors for display */
  let url = '/sources/' + action + '-manifest'
  console.log(url)
  console.log(data)
  $.ajax({
    method: 'POST',
    url: url,
    data: JSON.stringify(data),
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
          // window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      var msg = '<p>The manifest could not be saved because of the following errors:</p>'
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

  /* Handles the Display form */
  $('#go').click(function (e) {
    e.preventDefault()
    var name = $('#display').val()
    window.location = '/sources/display/' + name
  })
  $('#display').on('keypress', function (e) {
    e.preventDefault()
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
    $('#manifestForm').hide()
    $('#previewDisplay').show()
    var jsonform = cleanup() // jsonifyForm()
    $('#manifest').html(JSON.stringify(jsonform, null, '  '))
  })

  $('#hide').click(function (e) {
    e.preventDefault()
    $('#previewDisplay').hide()
    $('form').show()
  })

  /* Configure datepickers */
  // Currently does not accept datetime. Accepting either dates or
  // datetimes is a challenge. Try https://github.com/flatpickr/flatpickr
  var dateFormat = 'yy-mm-dd'
  var options = {
    dateFormat: dateFormat,
    constrainInput: false,
    changeMonth: true,
    changeYear: true,
    minDate: null,
    maxDate: null,
    onClose: function (date) {
      let isValid = checkDateFormat(date)
      // console.log('Date is valid: ' + isValid)
      // Check date range
      var container = $(this).closest('.form-group')
      var startField = container.children().find('input').eq(0)
      var endField = container.children().find('input').eq(1)
      var startDate = $.datepicker.parseDate('yy-mm-dd', startField.val())
      var endDate = $.datepicker.parseDate('yy-mm-dd', endField.val())
      // Valid date range
      if (endField.val().length === 0 || startDate <= endDate) {
        startField.attr('data-parsley-daterange', 'valid')
        endField.attr('data-parsley-daterange', 'valid')
      // Invalid date range
      } else {
        startField.attr('data-parsley-daterange', 'invalid')
        endField.attr('data-parsley-daterange', 'invalid')
      }
      startField.parsley().validate()
      endField.parsley().validate()
    }
  }
  // Set the row counters to 0
  sessionStorage.setItem('createdCounter', '0')
  sessionStorage.setItem('updatedCounter', '0')

  // Force datepickers below the input field
  // $.extend($.datepicker, {_checkOffset: function (inst, offset, isFixed) {return offset}})
  // Fine control for the datepicker location
  //  $.extend($.datepicker,{_checkOffset: function(inst, offset, isFixed) {offset.top = offset.top - 402; offset.left = offset.left - 240; return offset;}})

  // Get the date from a datepicker
  function getDate (element) {
    var date
    try {
      date = $.datepicker.parseDate(dateFormat, element.value)
    } catch (error) {
      date = null
    }
    return date
  }

  // Initialise all the datepickers on the page
  $('.datepicker').each(function () {
    let start
    let end
    start = $(this).datepicker(options)
      .on('change', function () {
        end.datepicker('option', 'minDate', getDate(this))
        $(this).datepicker('refresh')
      })
    end = $(this).datepicker(options)
      .on('change', function () {
        start.datepicker('option', 'maxDate', getDate(this))
        $(this).datepicker('refresh')
      })
  })

  $('#save').click(function (e) {
    e.preventDefault()
    // Show validation errors
    $('#manifestForm').parsley().validate({force: false})
    if ($('#manifestForm').parsley().isValid()) {
      saveManifest(cleanup(), 'create')
    }
  })

  // Add a date row by cloning the date template and setting its field names
  $(document).on('click', '.add-date', function () {
    let container = $(this).closest('.row')
    let rowType = $(this).data('row')
    let counter = parseInt(sessionStorage.getItem(rowType + 'Counter')) + uniqueId()
    sessionStorage.setItem(rowType + 'Counter', uniqueId())
    let $template = $('.date-template').clone()
    $template.attr('id', rowType + counter)
    $template.addClass('daterange')
    $template.addClass(rowType + '-row')
    $template.addClass(rowType + counter)
    $template.find('label').html(rowType).css('visibility', 'hidden')
    $template.find('.add-date').attr('data-row', rowType)
    $template.find('.remove-date').attr('data-row', rowType)
    $template.find('.remove-date').attr('data-count', rowType + counter)
    $template.find('input').eq(0).attr('id', rowType + '-start' + counter)
    $template.find('input').eq(0).attr('name', rowType + '-start' + counter)
    $template.find('input').eq(1).attr('id', rowType + '-end' + counter)
    $template.find('input').eq(1).attr('name', rowType + '-end' + counter)
    $template.find('input').removeClass('hasDatepicker')
    $template.removeClass('date-template').show().insertAfter(container)
  })

  // Trigger dynamically generated datepickers
  $(document).on('focus', '.datepicker', function () {
    if ($(this).hasClass('hasDatepicker') === false) {
      $(this).datepicker(options)
    } else {
      $(this).datepicker('destroy')
      $(this).datepicker(options)
    }
  })

  // Remove a date row
  $(document).on('click', '.remove-date', function () {
    let rowType = $(this).data('row')
    let id = $(this).data('count')
    let numRows = $('.' + rowType + '-row').length
    if (numRows > 1) {
      $('#' + id).remove()
      numRows = numRows - 1
      // Make sure the label is visible
      if (numRows === 1) {
        $('.' + rowType + '-row').find('label').css('visibility', 'visible')
      }
    } else {
      $('#' + id).find('.datepicker').datepicker('setDate', null)
    }
  })

  // Define all add buttons here, except for date fields
  const addBtns = ['add-author', 'add-note']
  const removeBtns = ['remove-author', 'remove-note']
  const assignments = {
    'author': {'elementName': 'authors', 'classes': ['authorName', 'authorGroup', 'authorOrg']},
    'note': {'elementName': 'notes', 'classes': ['note-field']}
  }

  // Add Field Function
  function addField (fieldType, id) {
    let previousRow = $('#' + id)
    // Clone the previous row with a unique id
    let uniqueId = Math.random().toString(36).substring(2) + (new Date()).getTime().toString(36)
    let clone = previousRow.clone().attr('id', fieldType + uniqueId)
    clone.attr('data-id', uniqueId)
    // Clear the values and the label
    clone.find('label').prop('for', fieldType + uniqueId).html('&nbsp;')
    clone.find('input:text').val('')
    clone.find('textarea').val('')
    clone.find('textarea').empty()
    // Insert the clone and remove the old row
    clone.insertAfter(previousRow)
  }

  // Remove Field Function
  function removeField (fieldType, id) {
    let row = $('#' + id)
    let numFields = $('[data-fieldtype="' + fieldType + '"]').length
    // If only one row is left
    if (numFields <= 1) {
      // Clone the template with a unique id
      let clone = row.clone().attr('id', fieldType + uniqueId())
      // Clear the values
      clone.find('input:text').val('')
      clone.find('textarea').val('')
      clone.find('textarea').empty()
      // Insert the clone and remove the old row
      clone.insertAfter(row)
      row.remove()
    } else {
      row.remove()
      numFields = $('[data-fieldtype="' + fieldType + '"]').length
      // Make sure the label is displayed if the first row is deleted
      if (numFields <= 1) {
        $('[data-fieldtype="' + fieldType + '"]').find('label').html(fieldType)
      }
    }
  }

  // Handle the Add Field Click Button
  $(document).on('click', '.add', function (e) {
    e.preventDefault()
    let fieldtype = $(this).closest('.row').attr('data-fieldtype')
    let id = $(this).closest('.row').attr('id')
    // Match add- in the button's classes
    for (const cls of this.classList) {
      if ($.inArray(cls, addBtns) !== -1) {
        // Call addField on the suffix of the add- class
        addField(fieldtype, id)
      }
    }
  })

  // Handle the Remove Field Click Button
  $(document).on('click', '.remove', function (e) {
    e.preventDefault()
    let fieldtype = $(this).closest('.row').attr('data-fieldtype')
    let id = $(this).closest('.row').attr('id')
    // Match remove- in the button's classes
    for (const cls of this.classList) {
      if ($.inArray(cls, removeBtns) !== -1) {
        // Call removeField on the suffix of the remove- class
        removeField(fieldtype, id)
      }
    }
  })

  // Blur from the field
  $(document).on('blur', '.author-field, .note-field', function () {
    // Re-serialise the text areas when the user clicks on another element
    let classes = this.className.split(' ')
    let cls = classes.find(item => /-field$/.test(item))
    let serialisedTextareas = serialiseTextareas('.' + cls)
    let key = cls.replace('-field', '')
    let el = assignments[key]['elementName']
    $('#' + el).val(serialisedTextareas)
    // console.log($('#' + el).val())
  })

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

  // End Property Cloning

  // Create Page Functions
  //

  //
  // Display Page Functions
  //

  /* Toggles the Edit/Update button and field disabled property */
  $('#update').click(function (e) {
    e.preventDefault()
    if ($('#update').attr('title') === 'Edit') {
      $('.form-check-label').removeClass('not-allowed')
      $('form').find('button, input, textarea, select, checkbox').each(function () {
        let fieldId = $(this).attr('id')
        if (fieldId !== 'name' && fieldId !== 'manifest-content') {
          $(this).prop('readonly', false)
          $(this).attr('readonly', false) // For select elements
          $(this).prop('disabled', false)
          $(this).removeClass('disabled')
        }
        if (fieldId === 'metapath') {
          $(this).prop('readonly', true)
          $(this).prop('disabled', true)
          $(this).addClass('disabled')
        }
      })
      $('#update').attr('title', 'Save')
      $('#update > i').removeClass('fa-pencil').addClass('fa-save')
    } else {
      var name = $('#name').val()
      bootbox.confirm({
        message: 'Are you sure you wish to update the record for <code>' + name + '</code>?',
        buttons: {
          confirm: { label: 'Yes', className: 'btn-success' },
          cancel: { label: 'No', className: 'btn-danger' }
        },
        callback: function (result) {
          if (result === true) {
            saveManifest(cleanup(), 'update')
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
        confirm: { label: 'Yes', className: 'btn-success' },
        cancel: { label: 'No', className: 'btn-danger' }
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
    if ($('#hideSearch').html() === 'Show Results') {
      $('#search-form').hide()
      $('#exportSearchResults').show()
      $('#results').show()
      $('#pagination').show()
      $('#hideSearch').html('Show Form')
    } else {
      $('#hideSearch').html('Show Results')
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
