(function ($) {
  $.fn.dateformat = function (settings) {
    settings = $.extend({ settingA: 'defaultA', settingB: 'defaultB' }, settings)
    var k = $(this).attr('id')
    let a = '#' + $(this).attr('id') + '_dateformat'
    let b = '#' + $(this).attr('id') + '_list'
    let p = a + ' :input'
    var jsontify = ''
    // let html = '<ol id="' + $(this).attr('id') + '_list"><li id="concatenate"><p class="datep" style="display:inline-block !important; width: 200px !important;">start date: <input id="' + $(this).attr('id') + '_ds_0" name="0" size="16" type="text" value="" class="datepicker date"></p><p class="datep" style="display:inline-block !important; width: 200px !important;">end date: <input id="' + $(this).attr('id') + '_de_0" name="0" size="16" type="text" value="" class="datepicker date "></p></li></ol><button id="add_date" type="button" class="btn btn-sm btn-outline-editorial">ADD DATE</button><button id="' + $(this).attr('id') + '_getdatevalue" type="button" class="btn btn-sm btn-outline-editorial">SUBMIT</button>'
    let html = '<ol id="' + $(this).attr('id') + '_list" style="list-style-type: none; padding: 0; margin: 0">'
    html += '<li id="concatenate"><div class="row">'
    html += '<div class="col-4"><input placeholder="Start Date" id="' + $(this).attr('id') + '_ds_0" name="0" size="16" type="text" value="" class="datepicker date"></div>'
    html += '<div class="col-4"><input placeholder="End Date" id="' + $(this).attr('id') + '_de_0" name="0" size="16" type="text" value="" class="datepicker date"></div>'
    html += '<div class="col-3" style="padding: 5px 5px;">'
    html += '<a id="add_date" role="button" class="btn btn-sm btn-outline-editorial" title="Add Date"><i class="fa fa-plus-circle"></i></a>'
    html += '<a role="button" class="remove_date btn btn-sm btn-outline-editorial" title="Remove Date"><i class="fa fa-minus-circle"></i></a>'
    html += '</div>'
    html += '</div></li>'
    html += '</ol>'

    $(a).append(html)

    $('.datepicker').datepicker({
      dateFormat: 'yy-mm-dd', // check change
      timeFormat: 'hh:mm:ss',
      constrainInput: false,
      onClose: function () {
        $(this).trigger('blur')
      }
    }).on('change', function () {
      if (moment($(this).val()).isValid()) {
        document.getElementById($(this).attr('id')).setAttribute('class', 'is-valid form-control datepicker date')
      } else if ($(this).val() === '') {
        document.getElementById($(this).attr('id')).setAttribute('class', 'datepicker date')
      } else {
        document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
      }
    })

    var counter = 0

    function dict(name, id, value) {
      this.name = name
      this.id = id
      this.value = value
    }

    function finaldate(start, end) {
      this.start = start
      this.end = end
    }

    function finaldate2(date) {
      this.date = date
    }

    $(document).on('click', '#add_date', function (e) {
      e.preventDefault()
      counter = counter + 1
      // let elem = '<li id="concatenate"><label class="col-form-label" for="ds_' + counter + '"></label><p class="datep" style="display:inline-block !important; width: 200px !important;">start date: <input id="' + $(this).attr('id') + '_ds_' + counter + '" name="' + counter + '" size="16" type="text" value="" class="datepicker date"></p><label class="col-form-label" for="de_' + counter + '"></label><p class="datep" style="display:inline-block !important; width: 200px !important;">end date: <input id="' + $(this).attr('id') + '_de_' + counter + '" name="' + counter + '" size="16" type="text" value="" class="datepicker date "></p><button type="button" class="remove_date btn btn-sm btn-outline-editorial">-</button></li>'
      let elem = '<li id="concatenate" style="padding-top: 5px;"><div class="row">'
      elem += '<div class="col-4"><input placeholder="Start Date" id="' + k + '_ds_' + counter + '" name=" ' + counter + ' " size="16" type="text" value="" class="datepicker date"></div>'
      elem += '<div class="col-4"><input placeholder="End Date" id="' + k + '_de_' + counter + '" name=" ' + counter + ' " size="16" type="text" value="" class="datepicker date"></div>'
      elem += '<div class="col-3" style="padding: 10px 5px;">'
      elem += '<a id="add_date" role="button" class="btn btn-sm btn-outline-editorial" title="Add Date"><i class="fa fa-plus-circle"></i></a>'
      elem += '<a role="button" class="remove_date btn btn-sm btn-outline-editorial" title="Remove Date"><i class="fa fa-minus-circle"></i></a>'
      elem += '</div>'
      elem += '</div></li>'

      $(b).append(elem)
      $('.datepicker').datepicker({
        dateFormat: 'yy-mm-dd', // check change
        timeFormat: 'hh:mm:ss',
        constrainInput: false,
        onClose: function () {
          $(this).trigger('blur')
        }
      }).on('change', function () {
        if (moment($(this).val()).isValid()) {
          document.getElementById($(this).attr('id')).setAttribute('class', 'is-valid form-control datepicker date')
        } else if ($(this).val() === '') {
          document.getElementById($(this).attr('id')).setAttribute('class', 'datepicker date')
        } else {
          document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
        }
      })
      // return false // prevent form submission
    })

    $(document).on('click', '.remove_date', function (e) {
      let z = b + ' li'
      e.preventDefault()
      if ($(z).children().size() > 1) {
        $(this).parent().parent().remove()
        var map = []
        var alerterror = 0
        $(p).map(function () {
          var date = new dict($(this).attr('name'), $(this).parents('li').index(), $(this).val())
          if (moment(date.value).isValid() || date.value === '') {
            sessionStorage.setItem(date.name, date.value)
            map.push(date)
          } else {
            document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
            if (alerterror < 1) {
              bootbox.alert('Please re-enter the correct format. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
            }
            date.value = 'invalid_format'
            map.push(date)
            alerterror++
          }
        })
        let values = []
        for (var i = 0; i < map.length / 2; i++) {
          let datestart = k + "_ds_" + i.toString()
          let dateend = k + "_de_" + i.toString()
          let item = new finaldate(sessionStorage.getItem(datestart), sessionStorage.getItem(dateend))
          values.push(item)
        }
        let s = ''
        values.forEach(function (m) {
          if (m.start !== "" && m.end !== "") {
            s = s + m.start + "," + m.end + "\r\n"
          }
          else {
            s = s + m.start + m.end + "\r\n"
          }
        })
        var parsevalue = []
        parsevalue = values
        parsevalue.forEach(function (i, index) {
          if (i.start == "" || i.end == "") {
            if (i.start !== '') {
              parsevalue[index] = i.start
            }
            else if (i.end !== '') {
              parsevalue[index] = i.end
            } else {
              parsevalue.pop(parsevalue[index])
            }
          }
        })

        s = s.substring(0, s.length - 2)
        jsontify = JSON.stringify(parsevalue)
        document.getElementById(k).value = s
        sessionStorage.setItem(k, jsontify)
      }
      else {
        $(this).attr('disabled', 'disabled')
      }
    })

    $(document).on('blur', '.datepicker', function () {
      let values = []
      var map = []
      var alerterror = 0
      // serialisedateformat($(this), $(this).attr('name'))
      $(p).map(function () {
        var date = new dict($(this).attr('id'), $(this).parents('li').index(), $(this).val())
        if (moment(date.value).isValid() || date.value === '') {
          sessionStorage.setItem(date.name, date.value)
          map.push(date)
        } else {
          document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
          if (alerterror < 1) {
            bootbox.alert('Please re-enter the correct format. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
          }
          date.value = 'invalid_format'
          map.push(date)
          alerterror++
        }
      })
      for (var i = 0; i < map.length / 2; i++) {
        let datestart = k + "_ds_" + i.toString()
        let dateend = k + "_de_" + i.toString()
        let item = new finaldate(sessionStorage.getItem(datestart), sessionStorage.getItem(dateend))
        values.push(item)
      }

      let s = ''
      values.forEach(function (m) {
        if (m.start !== "" && m.end !== "") {
          s = s + m.start + "," + m.end + "\r\n"
        }
        else {
          s = s + m.start + m.end + "\r\n"
        }
      })
      var parsevalue = []
      parsevalue = values
      parsevalue.forEach(function (i, index) {
        if (i.start == "" || i.end == "") {
          if (i.start !== '') {
            parsevalue[index] = i.start
          }
          else if (i.end !== '') {
            parsevalue[index] = i.end
          } else {
            parsevalue.pop(parsevalue[index])
          }
        }
      })

      s = s.substring(0, s.length - 2)
      jsontify = JSON.stringify(parsevalue)
      document.getElementById(k).value = s
      sessionStorage.setItem(k, jsontify)
    })


  } // end of plugin function
})(jQuery)
