$(document).ready(function () {
  $('.allres').click(function(e) {
    var key = $('.apikey');
    if (key.val() == '') {
      e.preventDefault();
      $('.msg').text('API key required to view results!');
    } else {
      $(this).attr('href', $(this).attr('href')+'?key='+key.val());
    }
  });

  $('#upload').click(function() {
    var formData = new FormData($('#fileupload')[0]);
    $('.msg').text('Processing...');
    $.ajax({
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        url: '/api/classify/topics',
        data: formData,
        contentType: false,
        processData: false,
        timeout: 0,
        success: function (data) {
          if (data.error) {
            $('.msg').text(data.error);
          } else {
            $('.msg').text('Done! ('+data.queries+'/'+data.limit+')');
            window.location.href = data.url;
          }
        },
        error: function (data) {
            alert('An error occured while uploading/processing!');
            $('.msg').text('');
        }
    });
  });
});
