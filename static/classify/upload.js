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
              if ((data.complete != data.total) && (data.status != 'cancelled')) {
                if (data.result.toLowerCase().indexOf('-assoc-') >= 0) {
                  $('.msg').text('Processing Association...');
                } else {
                  $('.msg').text('Processing... '+data.complete+'/'+data.total);
                }
                $('.apicalls').text('Used Today: '+data.apiused+' / '+data.apilimit);
              } else if (data.status == 'cancelled') {
                $('.msg').html('Cancelled last <a class="genlink tooltiplong" tip="'+data.result+'" href="'+data.url+'">File</a> ('+data.complete+')')
              }
              else {
                if (data.apiused) {
                  $('.apicalls').text('Used Today: '+data.apiused+' / '+data.apilimit);
                }
        				if (data.total) {
                        $('.msg').html('Finished last <a class="genlink tooltiplong" tip="'+data.result+'" href="'+data.url+'">File</a> ('+data.total+')');
        				} else {
        					$('.msg').text('');
        				}
                        $('.upload').text('Upload');
                        $('.upload').css({'background': '#2E7D32'});
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

  $('#upload').click(function(e) {
    e.preventDefault();
    if ($(this).text() == 'Upload') {
      var formData = new FormData($('#fileupload')[0]);
      $('.msg').text('Uploading...');
      $.ajax({
          type: 'POST',
          contentType: false,
          url: '/api/classify?catg=topics',
          data: formData,
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
