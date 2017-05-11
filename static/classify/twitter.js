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

  function checkqueue() {
    var key = $('.apikey').val();
    if (key != '') {
      $.ajax({
          type: 'GET',
          url: '/api/classify/check/'+key,
          success: function (data) {
            if (data.error) {
              $('.msg').text(data.error);
            } else {
        				if (data.status == 'complete' && ~data.status.indexOf('Twitter-')) {
                        $('.msg').html('Finished last <a class="genlink tooltiplong" tip="'+data.result+'" href="'+data.url+'">File</a> ('+data.total+')');
                        $('.upload').text('Submit');
                        $('.upload').css({'background': '#2E7D32'});
        				} else if (data.status == 'error') {
                        $('.msg').text('An error occurred during last request.');
                        $('.upload').text('Submit');
                        $('.upload').css({'background': '#2E7D32'});
                } else if (data.status == 'processing') {
          					    $('.msg').text('Processing...');
        				}

            }
          },
          error: function (data) {
              $('.msg').text('Error getting progress!');
          }
      });
    }
    setTimeout(checkqueue, 5000);
  }
  checkqueue();

  $('#searchtweet').click(function() {
    if ($(this).text() == 'Submit') {
      $('.msg').text('Submitting...');
      $.ajax({
          type: 'POST',
          contentType: 'application/json; charset=utf-8',
          url: '/api/classify/twitter',
          data: JSON.stringify({
                key: $('.apikey').val(),
                keywords: $('#keywords').val()
          }),
          processData: false,
          success: function (data) {
            if (data.error) {
              $('.msg').text(data.error);
            } else {
              if (data.status == 'processing') {
                $('.msg').text('Processing...');
                $('.upload').text('Cancel');
                $('.upload').css({'background': '#981e1e'});
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
                  $('.upload').text('Submit');
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
