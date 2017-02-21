$(document).ready(function () {
  $('#uploadassoc').click(function() {
    if ($(this).text() == 'Upload') {
      var formData = new FormData($('#fileupload')[0]);
      $('.msg').text('Uploading...');
      $.ajax({
          type: 'POST',
          contentType: 'application/json; charset=utf-8',
          url: '/api/classify/assoc',
          data: formData,
          contentType: false,
          processData: false,
          success: function (data) {
            if (data.error) {
              $('.msg').text(data.error);
            } else {
              if (data.status == 'processing') {
                $('.msg').text('Processing...');
                $('#uploadassoc').text('Cancel');
                $('#uploadassoc').css({'background': '#981e1e'});
              } else if (data.status == 'unavailable') {
                $('.msg').text('All workers are busy. Try again in a minute.');
              } else if (data.status == 'running') {
                $('.msg').text('Please wait for the other process to finsh.');
              }
            }
          },
          error: function (data) {
              alert('An error occured while uploading/processing!');
              $('.msg').text('');
          }
      });
    } else {
      var key = $('.apikey').val();
      if (key != '') {
        $.ajax({
            type: 'GET',
            url: '/api/classify/cancel/'+key,
            success: function (data) {
              if (data.error) {
                $('.msg').text(data.error);
              } else {
                  $('.msg').text('Remaining rows cancelled.');
                  $('.upload').text('Upload');
                  $('.upload').css({'background': '#2E7D32'});
              }
            },
            error: function (data) {
                $('.msg').text('Error cancelling!');
            }
        });
    }
  }
  });
});
