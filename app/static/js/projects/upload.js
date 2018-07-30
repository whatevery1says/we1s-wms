  // Upload Functions

  //
  // Dropzone implementation for uploading files
  //

$(document).ready(function () {

  /* Get the preview template and remove it from the DOM */
  var previewNode = document.querySelector('#template')
  previewNode.id = ''
  var previewTemplate = previewNode.parentNode.innerHTML
  previewNode.parentNode.removeChild(previewNode)

  /* Initiate the dropzone in the document body */
  var myDropzone = new Dropzone(document.body, {
    url: '/projects/import-project',
    acceptedFiles: '.zip',
    previewTemplate: previewTemplate,
    autoQueue: false, // Make sure the files aren't queued until manually added
    previewsContainer: '#previews', // Define the container to display the previews
    clickable: '.fileinput-button' // Define the element that should be used as click trigger to select files.
  })

  /* When an individual file is added, add the start button */
  myDropzone.on('addedfile', function(file) {
    $('#previews').show()
    file.previewElement.querySelector('.start').onclick = function() {
      myDropzone.enqueueFile(file)
    }
  })

  /* Update the total progress bar */
  myDropzone.on('totaluploadprogress', function(progress) {
    var bar = document.querySelector('#total-progress .progress-bar')
    bar.style.width = progress + '%'
  })

  /* Show the total progress bar when uploading starts */
  myDropzone.on('sending', function(file) {
    document.querySelector('#total-progress').style.opacity = '1'
     // And disable the start button 
    file.previewElement.querySelector('.start').setAttribute('disabled', 'disabled')
  })

  /* Show a response when the upload is done */
  myDropzone.on('complete', function(response) {
    // Make the back end response a parseable object 
    response = JSON.parse(response['xhr']['response'])
    if (response['errors'].length > 0) {
      // Show the errors
      msg = '<p>The following errors occurred:</p><ul>'
      $.each(response['errors'], function(index, value) {
        msg += '<li>' + value + '</li>'
      })
      msg += '</ul>'
    } else {
      // Or show success
      msg = 'The project was imported successfully.'
    }
    bootbox.alert(msg)
    myDropzone.removeAllFiles(true)
    /* Hide the total progress bar when nothing's uploading anymore */
    document.querySelector('#total-progress').style.opacity = '0'
  })

  /* Setup the buttons for all transfers.
     The "add files" button doesn't need to be setup because the config
     `clickable` has already been specified. */
  $('#actions .start').click(function() {
    myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED))
  })

}) /* End $(document).ready() */
