/* global moment */
/* eslint no-undef: "error" */
/* Parsley Validators */
window.Parsley.addValidator('datesformat', {
  validate: function (date) {
    let isValid
    if (date !== '' && date !== null) {
      if (moment(date, ['YYYY-MM-DD', moment.ISO_8601], true).isValid()) {
        isValid = true
      } else {
        isValid = false
      }
    }
    return isValid
  },
  messages: {
    en: 'Please use the format <code>yyyy-mm-dd</code> or <code>YYYY-MM-DDTHH:MM:SSZ</code>.'
  }
})
// Parsley-native invalid date range validator does not
// work because you can't access the trigger element
window.Parsley.addValidator('datesrange', {
  validate: function (value) {
    console.log('value: ' + value)
    let errorAdded = false
    $('.datepicker').each(function () {
      var container = $(this).closest('.form-group')
      var startField = container.children().find('input').eq(0)
      var endField = container.children().find('input').eq(1)
      var startVal = startField.val()
      var endVal = endField.val()
      try {
        var startDate = $.datepicker.parseDate('yy-mm-dd', startVal)
        var endDate = $.datepicker.parseDate('yy-mm-dd', endVal)
      } catch (e) {
        return true
      }
      // Valid date range
      if (endVal.length === 0 || startDate <= endDate) {
        startField.removeAttr('data-parsley-datesrange')
        endField.removeAttr('data-parsley-datesrange')
      // Invalid date range
      } else {
        startField.attr('data-parsley-datesrange', 'invalid')
        endField.attr('data-parsley-datesrange', 'invalid')
        errorAdded = true
      }
    })
    if (errorAdded === true) {
      return false
    }
  },
  messages: {
    en: 'The start date must precede the end date.'
  }
})
