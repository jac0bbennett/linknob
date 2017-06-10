$(window).load(function () {
  $('.loading').hide();
  $('#searchinput').attr('placeholder', 'Search');
});

titletext = $('title').text();

$(document).ready(function () {
    function checkint() {
      $.ajax({
          type: 'GET',
          contentType: 'application/json; charset=utf-8',
          url: '/api/checkinteract',
          async: true,
          data: JSON.stringify({}),
          dataType: 'json',
          success: function (data) {
              if (data.intcount != 0) {
                $('.intcount').text(data.intcount);
                $('title').text('(' + data.intcount + ') ' + titletext);
              }
          },
          error: function (data) {
          }
      });
      setTimeout(checkint, 24000);
    }
    checkint();
    $('a').click(function () {
      $.ajax({
          type: 'GET',
          contentType: 'application/json; charset=utf-8',
          url: '/api/getloadmsg',
          async: false,
          data: JSON.stringify({}),
          dataType: 'json',
          success: function (data) {
              $('.loading').show();
              $('#searchinput').attr('placeholder', data.loadmsg);
          },
          error: function (data) {
          }
      });
    });
    $('.noload').click(function() {
      $('.loading').hide();
      $('#searchinput').attr('placeholder', 'Search');
    });
    $('.graylink').click(function() {
      $('.loading').hide();
      $('#searchinput').attr('placeholder', 'Search');
    });
    $('.refblock a').click(function () {
      $('.loading, .loadinglabel').hide();
      $('#link_container, #statblock, .gencontent').show();
    });
    $('.infotitle a').click(function() {
      $('.loading').hide();
      $('#searchinput').attr('placeholder', 'Search');
    });
    $('#searchbar').submit(function () {
      $('.loading').show();
    });
    $('.toggle').click(function () {
        $('.addlnc').toggleClass('show');
        $(this).toggleClass('exitadd');
    });
    $('.cool').click(function () {
        var linkid = $(this).attr('data');
        var type = $(this).attr('data-pt-type');
        var self = $(this).text('---');
        var totalc = $(this);
        $(this).css({
            'background': '#C44437',
            'color': '#fff'
        });
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/addpoint/' + linkid,
            data: JSON.stringify({}),
            dataType: 'json',
            success: function (data) {
                var newcool = parseInt(totalc.attr('data-tc')) + 1;
                totalc.attr('data-tc', (parseInt(totalc.attr('data-tc')) + 1))
                $('.' + linkid).text(newcool);
                var newcoolcount = parseInt($('.selfcool').text()) - 1;
                $('.selfcool').text(newcoolcount);
                self.text(type)
                console.log('Worked!')
            },
            error: function (data) {
                alert('Oops your out of Cool Points. (Or you might need to sign in)');
            }
        });
    });
    $('.postedlinks a').click(function () {
        var linkid = $(this).attr('id');
        if (linkid == null) {
          linkid = $(this).attr('data-id');
        }
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/addclick',
            data: JSON.stringify({
              linkid: linkid
            }),
            dataType: 'json',
            success: function (data) {
            },
            error: function (data) {
                console.log('Error!')
            }
        });
    });

    $('.didipoint').click(function () {
        var linkid = $(this).attr('data-id');
        var self = $(this);
        var selftext = $(this).text();
        $.ajax({
            type: 'GET',
            contentType: 'application/json; charset=utf-8',
            url: '/api/pointcheck/' + linkid,
            data: JSON.stringify({}),
            dataType: 'json',
            success: function (data) {
                check = data.check;
                self.html(check + ' /<span class="totaltc" data-tc="' + linkid + '">' + selftext + '</span>');
            },
            error: function (data) {
                console.log('Error!')
            }
        });
    })

    $('.sublnc').click(function () {
        var comment = $('#comment').val();
        var link = $('#link').val();
        var ptname = $('#ptname').val();
        $('.sublnc').hide();
        $('.msg').text(' posting...');
        if (link == '') {
            $('.sublnc').show();
            $('.msg').text(' Link box cannot be blank!');
        } else {
          if (ptname.length > 20) {
            $('.sublnc').show();
            $('.msg').text(' Point name must be less than 20 characters!');
          }
          else {
            $.ajax({
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                url: '/i/addlnc',
                data: JSON.stringify({
                    comment: comment,
                    link: link,
                    ptname: ptname
                }),
                dataType: 'json',
                success: function (data) {
                    if (data.error) {
                      $('.sublnc').show();
                      $('.msg').html(data.error)
                    } else {
                      $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Posted!</span> reloading...');
                      location.reload();
                    }
                },
                error: function (data) {
                    $('.sublnc').show();
                    $('.msg').text(' Error posting!');
                }
            });
          }
        }
    });
    $('.subcomment').click(function () {
        var comment = $('.commentbox').val();
        var linkid = $(this).attr('data-id');
        var chainid = $(this).attr('data-c-id');
        $('.subcomment').hide();
        $('.commsg').text('posting...');
        if (comment == '') {
            $('.subcomment').show();
            $('.commsg').text(' Comment box cannot be blank!');
        } else {
            $.ajax({
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                url: '/i/addcomment',
                data: JSON.stringify({
                    comment: comment,
                    linkid: linkid,
                    chainid: chainid
                }),
                dataType: 'json',
                success: function (data) {
                    if (data.error) {
                      $('.subcomment').show();
                      $('.commsg').html(data.error)
                    } else {
                      $('.commsg').html(' <span style="color:#4CAF50;font-weight:400;">Posted!</span>');
                      $('.subcomment').show();
                      $('.commentbox').val('');
                      $('#commentthread').prepend('<span class="nowcomment" style="background:#f6e4c9;"><span id="com{{ comment.id }}"><a class="genlink" href="/'+data.user+'">'+data.user+'</a> <span class="graytext" style="font-size: 9pt;"> - just now</span><br><span class="graytext" style="margin-left:10px;">'+data.comment+'</span></span></span><br><br>');
                      setTimeout(function(){ $('.nowcomment').css('background','#fff');$('.nowcomment').removeClass('nowcomment'); },1500);
                    }
                },
                error: function (data) {
                    $('.subcomment').show();
                    $('.commsg').text(' Error posting!');
                }
            });
        }
    });
    $('.delcomment').click(function () {
        var comid = $(this).attr('data-id');
        var com = $('#com'+comid+' > .comtext');
        com.text('deleting...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/i/delcomment',
            data: JSON.stringify({
                comid: comid
            }),
            dataType: 'json',
            success: function (data) {
                if (data.error) {
                  $('.commsg').html(data.error)
                } else {
                  com.text('[Deleted]');
                  $
                }
            },
            error: function (data) {
                com.text(' Error deleting!');
            }
        });
    });
    $('.sublncchain').click(function () {
        var comment = $('#comment').val();
        var link = $('#link').val();
        var ptname = $('#ptname').val();
        var chainid = $(this).attr('data-c-id');
        var linkvis = $('input[name=visibility]:checked').val();
        if (linkvis == 'Public') {
          linkvis = 1
        } else if (linkvis == 'Unlisted') {
          linkvis = 2
        }
        $('.sublncchain').hide();
        $('.msg').text(' posting...');
        if (link == '') {
            $('.sublncchain').show();
            $('.msg').text(' Link box cannot be blank!');
        } else {
          if (ptname.length > 20) {
            $('.sublncchain').show();
            $('.msg').text(' Point name must be less than 20 characters!');
          }
          else {
            $.ajax({
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                url: '/i/newaddchain',
                data: JSON.stringify({
                    chainid: chainid,
                    comment: comment,
                    link: link,
                    ptname: ptname,
                    linkvis: linkvis
                }),
                dataType: 'json',
                success: function (data) {
                    if (data.error) {
                      $('.sublncchain').show();
                      $('.msg').html(data.error)
                    } else {
                      $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Posted!</span> reloading...');
                      location.reload();
                    }
                },
                error: function (data) {
                    $('.sublncchain').show();
                    $('.msg').text(' Error posting!');
                }
            });
          }
        }
    });
    $('.moreoptions').click(function () {
      if ($(this).text() == 'Options') {
        $(this).text('Close Options');
      }
      else {
        $(this).text('Options');
      }
      $('.moreoptionbox').toggle();
    });
    $('.addtochain').click(function () {
      if ($(this).text() == 'Add to Chain') {
        $(this).text('Close Chain');
      }
      else {
        $(this).text('Add to Chain');
      }
      $('.addtochainbox').toggle();
    });
    $('.addref').click(function () {
      if ($(this).text() == 'New Reference') {
        $(this).text('Close Reference');
      }
      else {
        $(this).text('New Reference');
      }
      $('.addrefbox').toggle();
    });
    $('.subrefbut').click(function () {
      var linkid = $('.subref').attr('data-id');
      var link = $('.subref').val();
      $('.subrefbut').hide();
      $('.msg').text(' adding...');
      if (link == '') {
          $('.subrefbut').show();
          $('.msg').text('Link box cannot be blank!');
      }
        else {
          $.ajax({
              type: 'POST',
              contentType: 'application/json; charset=utf-8',
              url: '/i/addref',
              data: JSON.stringify({
                  link: link,
                  linkid: linkid
              }),
              dataType: 'json',
              success: function (data) {
                  if (data.error) {
                    $('.subrefbut').show();
                    $('.msg').html(data.error)
                  } else {
                    $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Added!</span> reloading...')
                    location.reload();
                  }
              },
              error: function (data) {
                  $('.subrefbut').show();
                  $('.msg').text(' Error adding!');
              }
          });
        }
    });
    $('.sublinktochainbut').click(function () {
      var linkid = $('.sublinktochain').attr('data-id');
      var chaintitle = $('.sublinktochain').val();
      $('.sublinktochainbut').hide();
      $('.msg').text(' adding...');
      if (chaintitle == '') {
          $('..sublinktochainbut').show();
          $('.msg').text('Link box cannot be blank!');
      }
        else {
          $.ajax({
              type: 'POST',
              contentType: 'application/json; charset=utf-8',
              url: '/i/addchain',
              data: JSON.stringify({
                  chaintitle: chaintitle,
                  linkid: linkid
              }),
              dataType: 'json',
              success: function (data) {
                  if (data.error) {
                    $('.sublinktochainbut').show();
                    $('.msg').html(data.error)
                  } else {
                    $('.sublinktochainbut').show();
                    $('.sublinktochain').val('');
                    $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Added to '+chaintitle+'!</span>')
                  }
              },
              error: function (data) {
                  $('.sublinktochainbut').show();
                  $('.msg').text(' Error adding!');
              }
          });
        }
    });
    $('.subchain').click(function () {
      var chaintitle = $('#chaintitle').val();
      var chaindesc = $('#chaindesc').val();
      var chainvis = $('input[name=visibility]:checked').val();
      if (chainvis == 'Public') {
        chainvis = 1
      } else if (chainvis == 'Unlisted') {
        chainvis = 2
      }
      $('.subchain').hide();
      $('.msg').text(' creating...');
      if (chaintitle == '') {
          $('.subchain').show();
          $('.msg').text('Chain title cannot be blank!');
      }
        else {
          $.ajax({
              type: 'POST',
              contentType: 'application/json; charset=utf-8',
              url: '/i/newchain',
              data: JSON.stringify({
                  chaintitle: chaintitle,
                  chaindesc: chaindesc,
                  chainvis: chainvis
              }),
              dataType: 'json',
              success: function (data) {
                  if (data.error) {
                    $('.subchain').show();
                    $('.msg').html(data.error)
                  } else {
                    $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Created!</span> redirecting...')
                    window.location.href = 'https://www.linknob.com/c/'+data.uuid;
                  }
              },
              error: function (data) {
                  $('.subchain').show();
                  $('.msg').text(' Error creating!');
              }
          });
        }
    });
    $('.deletelink').click(function () {
        var pointloss = (parseInt($('.coolcount').text()) * 0.5).toString();
        $(this).text('Yes, DELETE! (-' + pointloss +' points)');
        $('.deletelink').click(function () {
        var linkid = $(this).attr('data-id');
        $('.loading').show();
        $('#searchinput').attr('placeholder', 'Deleting...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/delete',
            data: JSON.stringify({
                linkid: linkid
            }),
            dataType: 'json',
            success: function (data) {
                $('#links').html('<br><br><center><span style="color:#4CAF50;font-weight:400;font-size:24pt;font-family:Roboto;">Deleted!</span></center>');
                $('.loading').hide();
                $('#searchinput').attr('placeholder', 'Search');
            },
            error: function (data) {
                alert('An error occured!')
            }
        });
      });
    });
    $('.deletechain').click(function () {
        $(this).text('Click again to DELETE this chain!');
        $(this).css("float", "left");
        $('.deletechain').click(function () {
        var chainid = $(this).attr('data-id');
        $('.loading').show();
        $('#searchinput').attr('placeholder', 'Deleting...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/i/deletechain',
            data: JSON.stringify({
                chainid: chainid
            }),
            dataType: 'json',
            success: function (data) {
                $('#links').html('<br><br><center><span style="color:#4CAF50;font-weight:400;font-size:24pt;font-family:Roboto;">Deleted!</span></center>');
                $('.loading').hide();
                $('#searchinput').attr('placeholder', 'Search');
            },
            error: function (data) {
                alert('An error occured!')
            }
        });
      });
    });
    $('.savechain').click(function () {
        var chainid = $('deletechain').attr('data-id');
        var chainvis = $('input[name=visibility]:checked').val();
        if (chainvis == 'Public') {
          chainvis = 1
        } else if (chainvis == 'Unlisted') {
          chainvis = 2
        }
        $('.msg').html(' saving...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: window.location.href,
            data: JSON.stringify({
                chainid: chainid,
                chaintitle: $('.chaintitle').val(),
                chaindesc: $('.chaindesc').val(),
                chainvis: chainvis
            }),
            dataType: 'json',
            success: function (data) {
              if (data.error) {
                $('.savechain').show();
                $('.msg').html(data.error)
              } else {
                $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Saved!</span>');
                $('.chainsethead').text($('.chaintitle').val() + ' Settings');
                $('.savechain').show();
              }
            },
            error: function (data) {
                $('.msg').html('An error occured!');
            }
        });
    });
    $('.deleteref').click(function () {
        var linkid = $(this).attr('data-id');
        $('#' + linkid).html('<span class="msg">Deleting...<span>');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/deleteref',
            data: JSON.stringify({
                linkid: linkid
            }),
            dataType: 'json',
            success: function (data) {
                $('#' + linkid).html('<span class="msg">Deleted!<span>')
            },
            error: function (data) {
                alert('An error occured!')
            }
        });
    });
    $('.removelink').click(function () {
        var linkid = $(this).attr('data-id');
        var chainid = $(this).attr('data-c-id');
        $(this).text('Removing...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/i/removelfromc',
            data: JSON.stringify({
                chainid: chainid,
                linkid: linkid
            }),
            dataType: 'json',
            success: function (data) {
                $('.linkchainhead').html($('.linkchainhead').html()+' - <span style="color:#c82f2f;font-weight:400;">Removed!</span>');
                $('.removelink').html('<span style="color:#c82f2f;font-weight:400;">Removed!</span>');
            },
            error: function (data) {
                alert('An error occured!')
            }
        });
    });
    $('.recrawllink').click(function () {
        var linkid = $(this).attr('data-id');
        $('.loading').show();
        $('#searchinput').attr('placeholder', 'Crawling...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/crawl',
            data: JSON.stringify({
                linkid: linkid
            }),
            dataType: 'json',
            success: function (data) {
                location.reload();
            },
            error: function (data) {
                alert('An error occured!')
            }
        });
    });
    $('.sharelink').click(function () {
        var linkid = $(this).attr('shareid');
        $(this).html('<input type="text" class="shareinput" value="http://lknb.co/l/' + linkid + '">');
        $(this).removeClass('othtip');
        $('.shareinput').focus();
        $('.shareinput').select();
    });
    $('.follow-button').click(function () {
        userid = $(this).attr('data-userid');
        $('.unfollow-button').show();
        $('.follow-button').hide();
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/trail/' + userid,
            dataType: 'json',
            success: function (data) {},
            error: function (data) {
                alert('An error occured!')
            }
        });
    });
    $('.unfollow-button').click(function () {
        userid = $(this).attr('data-userid');
        $('.follow-button').show();
        $('.unfollow-button').hide();
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/api/trail/' + userid,
            dataType: 'json',
            success: function (data) {},
            error: function (data) {
                alert('An error occured!')
            }
        });
    });
    $('.unfollow-button').mouseenter(function () {
        $('.unfollow-button').html('&#x2717;Trailing');
    });
    $('.unfollow-button').mouseleave(function () {
        $('.unfollow-button').html('&#10003;Trailing');
    });
    $('.geninvite').click(function() {
      $.ajax({
          type: 'GET',
          contentType: 'application/json; charset=utf-8',
          url: '/api/geninvite',
          dataType: 'json',
          success: function (data) {
              $('<tr><td>' + data.code + '</td><td>Now</td><td>Active</td><td style="font-size:12pt;">http://linknob.com/signup?code=' + data.code + '</td></tr>').prependTo("table > tbody");
              var remains = $('#inviteremain').text();
              $('#inviteremain').text(parseInt(remains) - 1);
          },
          error: function (data) {
              alert('Out of Invites!')
          }
      });
    });
    $('.newdocsave').click(function () {
        var title = $('#pagetitle').val();
        var url = $('#pageurl').val();
        var header = $('#pageheader').val();
        var content = $('#pagecontent').html();
        var active = $('input[name=type]:checked').val();
        $('.msg').text('creating...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: '/i/newdoc',
            data: JSON.stringify({
                title: title,
                url: url,
                header: header,
                content: content,
                active: active
            }),
            dataType: 'json',
            success: function (data) {
              if (data.error) {
                $('.msg').text(data.error)
              } else {
                $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Created!</span>');
                window.location.href = 'https://www.linknob.com/d/'+url;
              }
            },
            error: function (data) {
                $('.msg').text('An error occured!');
            }
        });
    });
    $('.editdocsave').click(function () {
        var title = $('#pagetitle').val();
        var url = $('#pageurl').val();
        var header = $('#pageheader').val();
        var content = $('#pagecontent').html();
        var active = $('input[name=type]:checked').val();
        $('.msg').text('saving...');
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: window.location,
            data: JSON.stringify({
                title: title,
                url: url,
                header: header,
                content: content,
                active: active,
                deletedoc: false
            }),
            dataType: 'json',
            success: function (data) {
              if (data.error) {
                $('.msg').text(data.error)
              } else {
                $('.msg').html(' <span style="color:#4CAF50;font-weight:400;">Saved!</span>');
                window.location.href = '/i/editdoc/'+url;
              }
            },
            error: function (data) {
                $('.msg').text('An error occured!');
            }
        });
    });
    $('.deletedoc').click(function () {
        $.ajax({
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            url: window.location,
            data: JSON.stringify({
                deletedoc: true
            }),
            dataType: 'json',
            success: function (data) {
              if (data.error) {
                $('.msg').text(data.error)
              } else {
                $('#links').html('<span style="color:#4CAF50;font-weight:400;font-family:Roboto;">Deleted!</span>');
              }
            },
            error: function (data) {
                $('.msg').text('An error occured!');
            }
        });
    });
    $('.closepagealert').click(function () {
      $('.pagealert').hide();
        $.ajax({
            type: 'GET',
            contentType: 'application/json; charset=utf-8',
            url: '/api/closealert',
            dataType: 'json',
            success: function (data) {
            },
            error: function (data) {
                $('.msg').text('An error occured!');
            }
        });
    });
    $('.sigfor').submit(function() {
      $('.loading').show();
      $('#searchinput').attr('placeholder', 'Signing In...');
    });
});
