//
// Dropzone implementation for uploading files in Import
//

/* Get the preview template and remove it from the DOM */
var previewNode = document.querySelector('#template')
previewNode.id = ''
var previewTemplate = previewNode.parentNode.innerHTML
previewNode.parentNode.removeChild(previewNode)

/* Initiate the dropzone in the document body */
var myDropzone = new Dropzone (document.body, {
  url: '/corpus/upload/',
  acceptedFiles: '.json, .zip',
  thumbnailWidth: 80,
  thumbnailHeight: 80,
  parallelUploads: 20,
  previewTemplate: previewTemplate,
  autoQueue: false, // Make sure the files aren't queued until manually added
  previewsContainer: '#previews', // Define the container to display the previews
  clickable: '.fileinput-button' // Define the element that should be used as click trigger to select files.
})

/* When an individual file is added, add the start button */
myDropzone.on('addedfile', function (file) {
  file.previewElement.querySelector('.start').onclick = function () {
    myDropzone.enqueueFile(file)
  }
  $('.startUploads').removeClass('hidden')
  $('.cancelAll').removeClass('hidden')
})

/* Update the total progress bar */
myDropzone.on('totaluploadprogress', function (progress) {
  var bar = document.querySelector('#total-progress .progress-bar')
  bar.style.width = progress + '%'
})

/* Show the total progress bar when uploading starts */
myDropzone.on('sending', function (file) {
  document.querySelector('#total-progress').style.opacity = '1'
  /* And disable the start button */
  file.previewElement.querySelector('.start').setAttribute('disabled', 'disabled')
})

/* Send the form data to create the manifest. 
   Hide the total progress bar when nothing's uploading anymore. */
myDropzone.on('queuecomplete', function (progress) {
  document.querySelector('#total-progress').style.opacity = '0'
  var form = jsonifyForm ($('#metadataForm'))
  $.extend(form, {'import_dir': $('#token').val()})
  $.ajax({
    method: 'POST',
    url: '/corpus/save-upload',
    data: JSON.stringify(form),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      response = JSON.parse(response)
      if (response['errors']) {
        // alert(JSON.stringify(response['errors']))
        var errorFiles = []
        $.each(response['errors'], function (index, value) {
          value = value.replace('The <code>name</code> <strong>', '')
          value = value.replace('</strong> already exists in the database.', '')
          value += '.json'
          errorFiles.push(value)
        })
        $('[data-dz-name]').each(function () {
          if ($.inArray($(this).html(), errorFiles) !== -1) {
            $(this).next().html('The file could not be imported because a manifest with the same <code>name</code> already exists in the database.')
          }
        })
        var msg = '<p>The import contained one or more errors. See the individual files below for details.</p>'
        msg += '<p>' + JSON.stringify(errorFiles) + '</p>'
      } else {
        msg = '<p>The data was imported successfully.</p>'
      }
      bootbox.alert(msg)
    })
  // If no files are left in file list, reset the session token
  // and hide the startUploads and cancellAll buttons.
  if (myDropzone.getFilesWithStatus(Dropzone.ADDED).length === 0) {
    $('#session_token').val('')
    $('.startUploads').addClass('hidden')
    $('.cancelAll').addClass('hidden')
  }
})

/* When the cancel button is clicked, remove the file.
   Dropzone removes the file from the UI; the ajax removes
   it from session import directory. */
myDropzone.on('removedfile', function (file) {
  $.ajax({
    method: 'POST',
    url: '/corpus/remove-file',
    data: JSON.stringify({'filename': file.name}),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      console.log(JSON.parse(response)['response'])
    })
})

/* Delete all items from the queue and the session import directory. */
document.querySelector('#actions .cancelAll').onclick = function () {
  $.ajax({
    method: 'POST',
    url: '/corpus/remove-all-files',
    data: JSON.stringify({'file_list': myDropzone.files}),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      myDropzone.removeAllFiles(true)
      $('#session_token').val('')
      console.log(JSON.parse(response)['response'])
    })
}

/* Setup the buttons for all transfers.
   The "add files" button doesn't need to be setup because the config
   `clickable` has already been specified. */
document.querySelector('#actions .start').onclick = function () {
  myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED))
}
