/* Helper functions for the processing icon */
function showProcessing () {
  $('#processingIcon').show()
}
function hideProcessing () {
  $('#processingIcon').delay(500).hide(50)
}

/* Scripts loaded by base.html */
$(document).ready(function () {
  // Disable search field
  $('#search').submit(function (e) {
    e.preventDefault()
    alert('Search functionality has not yet been enabled.')
  })
  // Handle scroll to top
  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      $('#scroll').fadeIn()
    } else {
      $('#scroll').fadeOut()
    }
  })
  $('#scroll').click(function () {
    $('html, body').animate({ scrollTop: 0 }, 600)
    return false
  })

/*
  // Anando's javascript code for the functionality of the buttons "+", "submit", and "x".
  // Remove an input using the "x" button.
  $(document).on('click', '.remove', function () {
    $(this).parent().remove()
    return false // Prevent form submission
  })

  // The first one is the "submit" button for serialization.
  // authorsjs start
  $(document).on('click', '#author_serialize', function () {
    var store = ''
    var x = $('#aform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#authors').val(store)
    $('#aform').parent().remove()
    $('#authors').show()
    bootbox.alert('Your field has have been submitted.')
    console.log(store)
  })

  // This is the adding a new inputfield feature aka the "+". these repeat for the rest of the fields.
  // The only difference is their id names ,but functionality is pretty much the same. 
  $(document).on('click', '#add_author', function () {
    $('.author_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })
  // keywordjs start
  $(document).on('click', '#keyword_serialize', function () {
    var store = ''
    var x = $('#kform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#keywords').val(store)
    $('#kform').parent().remove()
    $('#keywords').show()
    bootbox.alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_keyword', function () {
    $('.keyword_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })
  // notejs start
  $(document).on('click', '#note_serialize', function () {
    var store = ''
    var x = $('#nform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#notes').show(store)
    $('#nform').parent().remove()
    $('#notes').show()
    bootbox.alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_note', function (e) {
    e.preventDefault()
    $('.note_field').append('<div><textarea name="sadface"></textarea><button class="btn rip remove btn-sm btn-outline-editorial"><i class="fa fa-minus-circle"></i></button></div>')
    // return false // Prevent form submission
  })

  // contributorsjs start
  $(document).on('click', '#contributor_serialize', function () {
    var store = ''
    var x = $('#cform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#contributors').val(store)
    $('#cform').parent().remove()
    $('#contributors').show()
    bootbox.alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_contributor', function () {
    $('.contributor_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })

  // licencesjs start
  $(document).on('click', '#license_serialize', function () {
    var store = ''
    var x = $('#lform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#licenses').val(store)
    $('#lform').parent().remove()
    $('#licenses').show()
    alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_license', function () {
    $('.license_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })

  // relationshipjs start
  $(document).on('click', '#relationships_serialize', function () {
    var store = ''
    var x = $('#rform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#relationships').val(store)
    $('#rform').parent().remove()
    $('#relationships').show()
    bootbox.alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_relationships', function () {
    $('.relationships_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })

  // sourcesjs start
  $(document).on('click', '#source_serialize', function () {
    var store = ''
    var x = $('#sform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#sources').val(store)
    $('#sform').parent().remove()
    $('#sources').show()
    alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_source', function () {
    $('.source_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })

  // processesjs start
  $(document).on('click', '#processes_serialize', function () {
    var store = ''
    var x = $('#pform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#processes').val(store)
    $('#pform').parent().remove()
    $('#processes').show()
    alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_processes', function () {
    $('.processes_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')   
    return false // Prevent form submission
  })

  // querytermsjs start
  $(document).on('click', '#queryterm_serialize', function () {
    var store = ''
    var x = $('#qform :input').serializeArray()
    console.log(x)
    $.each(x, function (i, field) {
      if (i === x.length - 1) {
        store = store + field.value
      } else {
        store = store + field.value + '\r'
      }
    })
    $('#queryterms').val(store)
    $('#qform').parent().remove()
    $('#queryterms').show()
    alert('Your field has have been submitted.')
    console.log(store)
  })

  $(document).on('click', '#add_queryterm', function () {
    $('.queryterm_field').append('<div><input name="sadface" type="textarea"><button class="btn rip remove btn-lg btn-outline-editorial">X</button></div>')
    return false // Prevent form submission
  })
  */
})
