/* Notes:
Everything seems to work, but validation/serialisation is untested. I need to integrate that into 
the form serialisation next.
*/

$(function () {
  // Configure datepickers
  const pickers = ['#created-start0', '#created-end0', '#updated-start0', '#updated-end0']
  var dateFormat = 'yy-mm-dd'
  var options = {
    dateFormat: dateFormat,
    constrainInput: false,
    changeMonth: true,
    changeYear: true,
    minDate: null,
    maxDate: null,
    onClose: function () {
      if (checkDateFormat($(this).val()) === false) {
        $(this).addClass('is-invalid')
        bootbox.alert('Please re-enter the correct format. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SSZ</code>.')
        // Otherwise, remove the error class
      } else {
        $(this).removeClass('is-invalid')
      }
    }
  }
  // Set the row counters to 0
  sessionStorage.setItem('createdCounter', '0')
  sessionStorage.setItem('updatedCounter', '0')

  // Force datepickers below the input field
  // $.extend($.datepicker, {_checkOffset: function (inst, offset, isFixed) {return offset}})
  // Fine control for the datepicker location
  //  $.extend($.datepicker,{_checkOffset: function(inst, offset, isFixed) {offset.top = offset.top - 402; offset.left = offset.left - 240; return offset;}})

  // Initialise all the datepickers on the page
  for (const picker of pickers) {
    let start
    let end
    start = $(picker).datepicker(options)
      .on('change', function () {
        end.datepicker('option', 'minDate', getDate(this))
      })
    end = $(picker).datepicker(options)
      .on('change', function () {
        start.datepicker('option', 'maxDate', getDate(this))
      })
  }
/*
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

  // Validate a single date for use when a single datepicker is closed
  function validDate (date) {
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

  // Add a date row by cloning the date template and setting its field names
  $(document).on('click', '.add-date', function () {
    let container = $(this).closest('.row')
    let rowType = $(this).data('row')
    let counter = parseInt(sessionStorage.getItem(rowType + 'Counter')) + 1
    sessionStorage.setItem(rowType + 'Counter', counter.toString())
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
    $template.removeClass('date-template').show().insertAfter(container)
  })

  // Trigger dynamically generated datepickers
  $(document).on('focus', '.datepicker', function () {
    $(this).datepicker(options)
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

  // Validate a date range row
  function validateDates (startField, endField, property) {
    let errors = []
    let start = startField.val()
    let end = endField.val()
    switch (true) {
      case start.length === 0 && end.length === 0:
        errors.push('Please delete the empty date row for the ' + property + ' property.')
        break
      case start.length > 0 && end.length === 0:
        if (!moment(start, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
          errors.push('A start field in the ' + property + ' property contains an invalid date type. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
        }
        break
      case start.length == 0 && end.length > 0:
        errors.push('Please enter a date in the empty ' + property + ' start field . Dates that are not date ranges should be entered in the start field, and the end field should be left empty.')
        break
      default:
        if (!moment(start, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
          errors.push('A start field in the ' + property + ' property contains an invalid date type. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
        }
        if (!moment(end, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
          errors.push('An end field in the ' + property + ' property contains an invalid date type. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
        }
    }
    // Make sure the start date precedes the end date
    if (!moment(start).isBefore(moment(end))) {
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
      if (moment(startDate, 'YYYY-MM-DDTHH:mm:ss', true).isValid()) {
        startDate = moment(startDate).toISOString()
      } else {
        startDate = moment(startDate).format('YYYY-MM-DD')
      }
      if (moment(endDate, 'YYYY-MM-DDTHH:mm:ss', true).isValid()) {
        endDate = moment(endDate).toISOString()
      } else {
        endDate = moment(endDate).format('YYYY-MM-DD')
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
      let result = validateDates(startDateField, endDateField, property)
      errors = errors + result
    })
    // If the dates are valid, serialise them
    if (errors.length === 0) {
      dates = serialiseDates()
    }
    return {'dates': dates, 'errors': errors}
  }

  // Preview button
  $(document).on('click', '.preview', function () {
    let result = processDates()
    if (result['errors'].length === 0) {
      // Extend the form
      console.log('Extend the form.')
    } else {
      bootbox.alert(JSON.stringify(result['errors']))
    }
  })*/
})
