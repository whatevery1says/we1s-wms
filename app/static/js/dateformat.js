(function ($) {
  $.fn.dateformat = function (settings) {
    settings = $.extend({ settingA: 'defaultA', settingB: 'defaultB' }, settings)
    var k = $(this).attr('id')
    let a = '#' + $(this).attr('id') + '_dateformat'
    let b = '#' + $(this).attr('id') + '_list'
    let p = a + ' :input'
    // var values = []
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

    $(document).on('click', '#add_date', function (e) {
      e.preventDefault()
      counter = counter + 1
      // let elem = '<li id="concatenate"><label class="col-form-label" for="ds_' + counter + '"></label><p class="datep" style="display:inline-block !important; width: 200px !important;">start date: <input id="' + $(this).attr('id') + '_ds_' + counter + '" name="' + counter + '" size="16" type="text" value="" class="datepicker date"></p><label class="col-form-label" for="de_' + counter + '"></label><p class="datep" style="display:inline-block !important; width: 200px !important;">end date: <input id="' + $(this).attr('id') + '_de_' + counter + '" name="' + counter + '" size="16" type="text" value="" class="datepicker date "></p><button type="button" class="remove_date btn btn-sm btn-outline-editorial">-</button></li>'
      let elem = '<li id="concatenate" style="padding-top: 5px;"><div class="row">'
      elem += '<div class="col-4"><input placeholder="Start Date" id="' + $(this).attr('id') + '_ds_' + counter + '" name=" ' + counter + ' " size="16" type="text" value="" class="datepicker date"></div>'
      elem += '<div class="col-4"><input placeholder="End Date" id="' + $(this).attr('id') + '_de_' + counter + '" name=" ' + counter + ' " size="16" type="text" value="" class="datepicker date"></div>'
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
        var s = ''
        let t = 0
        for (var i = 1; i < map.length; i++) {
          switch (true) {
            case (map[i].value === ''):
              if (map[i].id !== map[i - 1].id) {
                t = 1
              }
              s = s + ''
              break
            case (map[i].value !== ''):
              if (map[i].name !== map[i - 1].name) {
                s = s + '\r\n' + map[i].value
              } else {
                if (map[i].id !== map[i - 1].id || t === 1) {
                  s = s + '\r\n' + map[i].value
                } else {
                  s = s + ',' + map[i].value
                }
              }
              break
          }
        }
        s = map[0].value + s
        document.getElementById(k).value = s
      }
      else {
        $(this).attr('disabled', 'disabled')
      }
    })

    // $(d).click(function () {
    //   var map = []
    //   var alerterror = 0
    //   $(p).map(function () {
    //     console.log($(this).parents('li').index() + ' ' + $(this).val())
    //     var date = new dict($(this).attr('name'), $(this).parents('li').index(), $(this).val())
    //     if (moment(date.value).isValid() || date.value === '') {
    //       map.push(date)
    //     } else {
    //       document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
    //       if (alerterror < 1) {
    //         bootbox.alert('Please re-enter the correct format. Valid formats are <code>YYYY-MM-DD</code> and <code>YYYY-MM-DDTHH:MM:SS</code>.')
    //       }
    //       date.value = 'invalid_format'
    //       map.push(date)
    //       alerterror++
    //     }
    //   })
    //   var s = ''
    //   let t = 0
    //   for (var i = 1; i < map.length; i++) {
    //     switch (true) {
    //       case (map[i].value === ''):
    //         if (map[i].id !== map[i - 1].id) {
    //           t = 1
    //         }
    //         s = s + ''
    //         break
    //       case (map[i].value !== ''):
    //         if (map[i].name !== map[i - 1].name) {
    //           s = s + '\r\n' + map[i].value
    //         } else {
    //           if (map[i].id !== map[i - 1].id || t === 1) {
    //             s = s + '\r\n' + map[i].value
    //           } else {
    //             s = s + ',' + map[i].value
    //           }
    //         }
    //         break
    //     }
    //   }
    //   s = map[0].value + s
    //   document.getElementById(k).value = s
    // })

    $(document).on('blur', '.datepicker', function () {
      var map = []
      var alerterror = 0
      // serialisedateformat($(this), values)
      $(p).map(function () {
        var date = new dict($(this).attr('name'), $(this).parents('li').index(), $(this).val())
        if (moment(date.value).isValid() || date.value === '') {
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
      var s = ''
      let t = 0
      for (var i = 1; i < map.length; i++) {
        switch (true) {
          case (map[i].value === ''):
            if (map[i].id !== map[i - 1].id) {
              t = 1
            }
            s = s + ''
            break
          case (map[i].value !== ''):
            if (map[i].name !== map[i - 1].name) {
              s = s + '\r\n' + map[i].value
            } else {
              if (map[i].id !== map[i - 1].id || t === 1) {
                s = s + '\r\n' + map[i].value
              } else {
                s = s + ',' + map[i].value
              }
            }
            break
        }
      }
      s = map[0].value + s
      document.getElementById(k).value = s
    })
  } // end of plugin function
})(jQuery)



// function serialisedateformat (gval, values) {
//   let substr1 = 'ds'
//   let substr2 = 'de'
//   let item = {start: "", end: ""}
//   values.push(item)
//   let val = values[0]
//   $(gval).each(function () {

//     if (this.value !== '') {
//       switch (true) {
//         case ($(this).attr('id').includes(substr1)):
//           val['start'] = this.value
//           break

//         case ($(this).attr('id').includes(substr2)):
//           val['end'] = this.value
//           break
//       }
//     }
//   })
//   console.log(values)
//   return JSON.stringify(values)
// }