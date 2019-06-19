/* global bootbox, hideProcessing, moment, removeQueryBuilder, searchCorpus, showProcessing */
/* eslint no-undef: "error" */
//
// General Helper Functions
//

function jsonifyForm (formObj) {
  /* Handles JSON form serialisation */
  var form = {}
  let getform = '#' + formObj.attr('id') + ' *'
  $.each($(getform).not('.datepicker').serializeArray(), function (_, field) {
    form[field.name] = field.value || ''
  })
  return form
}

function getFormvals () {
  /* Get all form values, even disabled ones */
  let formvals = {}
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
  return formvals
}

function uniqueId () {
  /* Return a unique ID */
  return Math.random().toString(36).substring(2) + (new Date()).getTime().toString(36)
}

//
// Ajax Functions
//

function saveProject (manifest, action, newName = null, version = null) {
  /* Creates a new manifest
  Input: A JSON serialisation of the form values
  Returns: A copy of the manifest and an array of errors for display */
  let data = {'manifest': manifest, 'action': action}
  let url = '/projects/save'
  if ($('#update').html() === 'Update' || newName !== null) {
    url = '/projects/save-as'
    data['path'] = null
    data['new_name'] = newName
    data['version'] = version
  }
  $.ajax({
    method: 'POST',
    url: url,
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var errors = JSON.parse(response)['errors']
      if (errors.length === 0) {
        console.log(response)
        var manifest = JSON.parse(response)['manifest']
        var msg = '<p>Saved the following manifest:</p>' + manifest
        bootbox.alert({
          message: msg,
          callback: function () {
            if (action === 'create') {
              window.location = '/projects/display/' + manifest['_id']
            } else {
              removeQueryBuilder()
            }
          }
        })
      } else {
        msg = '<p>Could not save the manifest because of the following errors:</p>' + errors
        bootbox.alert(msg)
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      var msg = '<p>The manifest could not be saved because of the following errors:</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function deleteProject (manifest, versionNumber = null) {
  /* Deletes a project or project version
   Input: A manifest and a version_number
   Returns: An array of errors for display */
  let data = {'manifest': manifest, 'version': versionNumber}
  $.ajax({
    method: 'POST',
    url: '/projects/delete',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var errors = JSON.parse(response)['errors']
      if (errors.length > 0) {
        bootbox.alert('<p>Could not delete the version because of the following errors:</p>' + errors)
      } else {
        // Delete the row in the UI
        $('#workflow' + versionNumber).remove()
        // Get the hidden content value as an object
        let dataStr = $('#versions').val().replace(/'/g, '"')
        let data = JSON.parse(dataStr)
        // Find the index of the object to remove and delete it
        let index = data.findIndex(x => x.version_number === versionNumber)
        data.splice(index, 1)
        // Update the hidden content value
        $('#versions').val(JSON.stringify(data))
        // Just for testing
        // console.log(JSON.stringify(data))
        bootbox.alert('<p>The version was deleted.</p>')
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      var msg = '<p>The version could not be deleted because of the following errors:</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function exportProject (manifest, version = null) {
  /* Exports a version datapackage from a project
   Input: A manifest and a version_number
   Returns: An array of errors for display */
  let data = {'manifest': manifest, 'version_number': version}
  $.ajax({
    method: 'POST',
    url: '/projects/export',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var errors = JSON.parse(response)['errors']
      if (errors.length > 0) {
        bootbox.alert('<p>Could not export the version because of the following errors:</p>' + errors)
      } else {
        window.location = '/projects/download-export/' + response['filename']
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      var msg = '<p>The version could not be exported because of the following errors:</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

/* function exportSearch (data) {
   Exports the results of a Projects search
     Input: Values from the search form
     Returns: An array containing results and errors for display
  $.ajax({
    method: 'POST',
    url: '/projects/export-search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      response = JSON.parse(response)
      if (response['errors'].length !== 0) {
        var result = JSON.stringify(response['errors'])
        bootbox.alert('<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>')
      } else {
        window.location = '/projects/download-export/' + response['filename']
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
} */

// function searchProjects (data) {
//   /* Searches the Projects database
//      Input: Values from the search form
//      Returns: An array containing results and errors for display */
//   $.ajax({
//     method: 'POST',
//     url: '/projects/search',
//     data: JSON.stringify(data),
//     contentType: 'application/json;charset=UTF-8',
//     beforeSend: showProcessing()
//   })
//     .done(function (response) {
//       $('#results').empty()
//       hideProcessing()
//       response = JSON.parse(response)
//       if (response['errors'].length !== 0) {
//         var result = response['errors']
//         var message = ''
//         $.each(result, function (i, item) {
//           message += '<p>' + item + '</p>'
//         })
//         bootbox.alert({
//           message: message
//         })
//       } else {
//         result = response['response']
//         // Make the result into a string
//         var out = ''
//         $.each(result, function (i, item) {
//           var link = '/projects/display/' + item['_id']
//           out += '<h4><a href="' + link + '">' + item['name'] + '</a></h4><br>'
//           $.each(item, function (key, value) {
//             value = JSON.stringify(value)
//             if (key === 'content' && value.length > 200) {
//               value = value.substring(0, 200) + '...'
//             }
//             out += '<code>' + key + '</code>: ' + value + '<br>'
//           })
//           out += '<hr>'
//         })
//         var $pagination = $('#pagination')
//         var defaultOpts = {
//           visiblePages: 5,
//           initiateStartPageClick: false,
//           onPageClick: function (event, page) {
//             var newdata = {
//               'query': $('#query').val(),
//               'regex': $('#regex').is(':checked'),
//               'limit': $('#limit').val(),
//               'properties': $('#properties').val(),
//               'page': page
//             }
//             searchCorpus(newdata)
//             $('#scroll').click()
//           }
//         }
//         var totalPages = parseInt(response['num_pages'])
//         var currentPage = $pagination.twbsPagination('getCurrentPage')
//         $pagination.twbsPagination('destroy')
//         $pagination.twbsPagination($.extend({}, defaultOpts, {
//           startPage: currentPage,
//           totalPages: totalPages
//         }))
//         $('#results').append(out)
//         $('#hideSearch').removeClass('hidden')
//         $('#hideSearch').html('Show Form')
//         $('#exportSearchResults').show()
//         $('#search-form').hide()
//         $('#results').show()
//         $('#pagination').show()
//       }
//     })
//     .fail(function (jqXHR, textStatus, errorThrown) {
//       hideProcessing()
//       var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
//       msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
//       bootbox.alert(msg)
//     })
// }

function sendExport (jsonform) {
  /* Sends the export options to the server
     Input: A serialised set of form values from the export modal
     Returns: The name of the file to download.
     Automatically redirects to the download function. */
  $.ajax({
    method: 'POST',
    url: '/projects/send-export',
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
      window.location = '/projects/download-export/' + filename
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      hideProcessing()
      var msg = '<p>Sorry, mate! You\'ve got an error!</p>'
      msg += '<p>' + textStatus + ': ' + errorThrown + '</p>'
      bootbox.alert(msg)
    })
}

function launch (workflow, manifest, version = null, newProject = true) {
  /* Launches a new workflow in the Virtual Workspace
  Input: The name of the workflow, the project manifest,
         an optional version number, and a Boolean indicating 
         a new project
  Returns: An array of errors for display */
  let data = {'workflow': workflow, 'manifest': manifest, 'version': version, 'new': newProject}
  $.ajax({
    method: 'POST',
    url: '/projects/launch',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8',
    beforeSend: showProcessing()
  })
    .done(function (response) {
      hideProcessing()
      var errors = JSON.parse(response)['errors']
      if (errors.length > 0) {
        var msg = '<p>The project could not be launched because of the following errors:</p><ul>'
        $.each(errors, function (_, value) {
          msg += '<li>' + value + '</li>'
        })
        msg += '</ul>'
        bootbox.alert(msg)
      } else {
        window.open(JSON.parse(response)['filepath'], '_blank')
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      var msg = '<p>The project could not be launched because of the following errors:</p>'
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

/*
    This should handle all cloneable fields in create, except for dates.
*/

// Define all add buttons here
const addBtns = ['add-contributor', 'add-license', 'add-note']
const removeBtns = ['remove-contributor', 'remove-license', 'remove-note']
const assignments = {
  'contributor': {'elementName': 'contributors', 'classes': ['contributorTitle', 'contributorGroup', 'contributorOrg', 'contributorPath', 'contributorEmail', 'contributorRole']},
  'license': {'elementName': 'licenses', 'classes': ['licenseName', 'licensePath', 'licenseTitle']},
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
  clone.find('label').html('&nbsp;')
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
$(document).on('blur', '.contributor-field, .license-field, .note-field', function () {
  // Re-serialise the text areas when the user clicks on another element
  let classes = this.className.split(' ')
  let cls = classes.find(item => /-field$/.test(item))
  let serialisedTextareas = serialiseTextareas('.' + cls)
  let key = cls.replace('-field', '')
  let el = assignments[key]['elementName']
  $('#' + el).val(serialisedTextareas)
  // console.log($('#' + el).val())
})
// End Property Cloning

//
// $(function () { Event Handling
//

$(function () {
  //
  // Index Page Functions
  //

  /* Handles the Display form on the index page */
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

  //
  // Create and Display Page Functions
  //

  // Configure datepickers
  // Currently does not accept datetime. Need to install the datetimepicker plugin
  var dateFormat = 'yy-mm-dd'
  var options = {
    dateFormat: dateFormat,
    constrainInput: false,
    changeMonth: true,
    changeYear: true,
    minDate: null,
    maxDate: null,
    onClose: function (date) {
      // let isValid = checkDateFormat(date)
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

  /* Deprecated - Validate a single date for use when a single datepicker is closed
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
  } */

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

  // Validate a date range row
  function validateDates (startField, endField, property) {
    let errors = []
    let start = startField.val()
    let end = ''
    if (endField.length > 0) {
      end = endField.val()
    }
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
    var dates = {
      'created': [],
      'updated': []
    }
    $('.daterange').each(function () {
      var date
      if ($(this).attr('id') === 'created0') {
        var fieldType = 'created'
      } else {
        fieldType = $(this).find('button').first().data('row')
      }
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
      if (endDate !== undefined) {
        if (moment(endDate, 'YYYY-MM-DDTHH:mm:ss', true).isValid()) {
          endDate = moment(endDate).toISOString()
        } else {
          endDate = moment(endDate).format('YYYY-MM-DD')
        }
      }
      if (endDate === 'Invalid date') {
        endDate = null
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

  function processDates () {
    let dates = []
    let errors = []
    $('.daterange').each(function () {
      // Validate all dates
      let property = $(this).find('button').first().data('row')
      let startDateField = $(this).find('input').eq(0)
      let endDateField = $(this).find('input').eq(1)
      if (endDateField.length === 0) {
        endDateField = ''
      }
      let result = validateDates(startDateField, endDateField, property)
      errors = errors.concat(result)
    })
    // If the dates are valid, serialise them
    if (errors.length === 0) {
      dates = serialiseDates()
    }
    return {'dates': dates, 'errors': errors}
  }

  function cleanup () {
    /* Serialises the form values and converts strings in hidden fields and 
    session storage to proper JSON format. */
    const form = jsonifyForm($('#manifestForm'))
    $.extend(form, {'name': $('#name').val(), 'metapath': $('#metapath').val()})
    const newform = {}
    const clones = ['contributors', 'licenses', 'notes']
    let prefixes = {
      'contributors': 'contributor',
      'licenses': 'license'
    }
    const csvs = ['keywords']
    const checkboxes = []
    const lists = ['notes']
    const exclude = [
      'contributorTitle', 'contributorOrg', 'contributorGroup', 'contributorPath',
      'contributorEmail', 'contributorRole', 'licenseName', 'licensePath',
      'licenseTitle', 'notesField'
    ]
    // Use pipes for multiple patterns
    const excludePatterns = new RegExp('^builder_rule_')
    // NB. Relationships are not yet handled because they may be erroneously assigned to
    // RawData in the schema.
    // Copy the form values, ommitting empty fields and exclusions
    $.each(form, function (key, value) {
      if (value !== '' && value !== [] && !key.match(excludePatterns) && $.inArray(key, exclude) === -1) {
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

  /* Handles the manifest preview and hide buttons */
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

  /* Handles Save Button */
  $('#save').click(function (e) {
    e.preventDefault()
    // Show validation errors
    $('#manifestForm').parsley().validate({force: false})
    if ($('#manifestForm').parsley().isValid()) {
      saveProject(cleanup(), $(this).attr('data-action'))
    }
  })

  /* Handles the Launch button */
  $('.dropdown-item').click(function (e) {
    e.preventDefault()
    let workflow = $(this).attr('id').replace('-btn', '')
    var query = $('#builder').queryBuilder('getMongo')
    if (query == null) {
      bootbox.alert('To launch the project you must first supply a database query in the Data Resources tab.')
    } else {
      launch(workflow, getFormvals())
    }
  })

  /* Handles the Version Launch button */
  $('.export-version').click(function (e) {
    e.preventDefault()
    var versionNumber = $(this).attr('id').replace('launch', '')
    launch(cleanup(), versionNumber)
  })

  //
  // Create Page Functions
  //

  //
  // Display Page Functions
  //

  /* Makes the global template available to scripts for the display page */
  var globalTemplate = $('#global-template').html() // eslint-disable-line no-unused-vars

  /* Toggles the Edit/Update button and field disabled property */
  $('#update').click(function (e) {
    e.preventDefault()
    if ($('#update').attr('title') === 'Edit Project') {
      $('.form-check-label').removeClass('not-allowed')
      $('form').find('button, input, textarea, select, checkbox').each(function () {
        let fieldId = $(this).attr('id')
        if (fieldId !== 'name' && fieldId !== 'manifest-content' && fieldId !== 'created') {
          $(this).prop('readonly', false)
          $(this).prop('disabled', false)
          $(this).removeClass('disabled')
        }
        if (fieldId === 'metapath' || fieldId === '_id') {
          $(this).prop('readonly', true)
          $(this).prop('disabled', true)
          $(this).addClass('disabled')
        }
      })
      if (!$('#datapackageRow').length) {
        $('#query-builder-row').show()
      }
      $('#update').attr('title', 'Update Project')
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
            saveProject(cleanup(), 'update')
          }
        }
      })
    }
  })

  /* Handles the Clone Button */
  $('#clone').click(function (e) {
    e.preventDefault()
    bootbox.prompt({
      title: 'Enter the name of the new project.',
      buttons: {
        confirm: { label: 'Save', className: 'btn-success' },
        cancel: { label: 'Cancel', className: 'btn-danger' }
      },
      callback: function (result) {
        var regex = RegExp('[^a-z0-9_-]')
        if (regex.test(result)) {
          let msg = '<p class="text-danger">Project names must contain only lower-case alphanumeric characters, plus "-" and "_".</p>'
          $('.modal-body').append(msg)
        } else {
          saveProject(cleanup(), 'create', result)
          bootbox.hideAll()
        }
        return false
      }
    })
  })

  /* Handles the Clone Version Button */
  $('.clone-version').click(function (e) {
    e.preventDefault()
    var versionNumber = $(this).attr('id').replace('clone', '')
    bootbox.prompt({
      title: 'Enter the name of the new project.',
      buttons: {
        confirm: { label: 'Save', className: 'btn-success' },
        cancel: { label: 'Cancel', className: 'btn-danger' }
      },
      callback: function (result) {
        var regex = RegExp('[^a-z0-9_-]')
        if (regex.test(result)) {
          let msg = '<p class="text-danger">Project names must contain only lower-case alphanumeric characters, plus "-" and "_".</p>'
          $('.modal-body').append(msg)
        } else {
          saveProject(cleanup(), 'create', result, versionNumber)
          bootbox.hideAll()
        }
        return false
      }
    })
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
          deleteProject(name, metapath)
        }
      }
    })
  })

  /* Handles the Version Delete button */
  $('.delete-version').click(function (e) {
    e.preventDefault()
    var versionNumber = $(this).attr('id').replace('delete', '')
    bootbox.confirm({
      message: 'Are you sure you wish to delete version' + versionNumber + '?',
      buttons: {
        confirm: { label: 'Yes', className: 'btn-success' },
        cancel: { label: 'No', className: 'btn-danger' }
      },
      callback: function (result) {
        if (result === true) {
          deleteProject(cleanup(), versionNumber)
        }
      }
    })
  })

  /* Handles the Version Export button */
  $('.export-version').click(function (e) {
    e.preventDefault()
    var versionNumber = $(this).attr('id').replace('export', '')
    exportProject(cleanup(), versionNumber)
  })

  /* Handles the Export feature */
  $('#export').click(function (e) {
    e.preventDefault()
    if ($('#update').html() === 'Update') {
      bootbox.alert('Make sure you have saved your updates before exporting.')
    } else {
      exportProject(cleanup(), null)
    }
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
    var opts = { 'exportoptions': [] }
    $('.exportchoice:checked').each(function () {
      opts['exportoptions'].push(this.value)
    })
    // Doesn't work on disabled fields
    // var jsonform = jsonifyForm($('#manifestForm'))
    // $.extend(jsonform, opts)
    // Works on disabled fields
    let formvals = {}
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
    $.extend(formvals, opts)
    sendExport(formvals)
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
    searchCorpus(data)
  })

  $('#manifestForm').parsley()
}) /* End of $(document).ready() Event Handling */
