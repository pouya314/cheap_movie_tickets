$(function() {
  var result_el = $('.result');

  function retrieve_data() {
    result_el.html('<div class="text-center">Processing...</div>');

    $.ajax({
      method: "GET",
      url: $SCRIPT_ROOT + "/get_cheapest_tickets",
      contentType: 'application/json;charset=UTF-8',

      success: function( data ) {
        if (data.result) {
          var source = document.getElementById("entry-template").innerHTML;
          var template = Handlebars.compile(source);
          var context = {
            movies: data.result.movies, 
            updated_at: data.result.updated_at
          };
          var content = template(context);
          result_el.html(content);
        } else {
          result_el.html('<div class="text-center">Requesting fresh data...</div>');
          request_fresh_data();
        }
      },
      error: function( e ) {
        result_el.html('<div class="text-center">Something went wrong! Please try again!</div>');
      }
    });
    return false;
  }

  function disableButtons() {
    $("#refresh-data").attr('disabled', true);
    $('#get-tickets').attr('disabled', true);
  }
  function enableButtons() {
    $("#refresh-data").attr('disabled', false);
    $('#get-tickets').attr('disabled', false);
  }

  function request_fresh_data() {
    disableButtons();
    $.ajax({
      method: "POST",
      url: $SCRIPT_ROOT + "/request_fresh_data",
      contentType: 'application/json;charset=UTF-8',

      success: function( data ) {
        var job_id = data.job_id;
        result_el.html(
          '<div class="text-center">Your request is being Processed! This may take a few minutes...</div><div class="loader">Loading</div>'
        );

        var interval_id = setInterval(function() {
          $.ajax({
            method: "GET",
            url: $SCRIPT_ROOT + "/get_job_status/"+job_id,
            contentType: 'application/json;charset=UTF-8',

            success: function( data ) {
              var status = data.status;

              if (status == "success") {
                clearInterval(interval_id);
                enableButtons();
                retrieve_data();
              } else if (status == "fail") {
                clearInterval(interval_id);
                enableButtons();
                result_el.html('<div class="text-center">Could not get updated movie data.. Please try again!</div>');
              } else if (status == "pending") {
                // Do nothing 
              } else {
                console.log('unknown status!')
                enableButtons();
                clearInterval(interval_id);
              }
            },
            error: function( e ) {
              result_el.html('<div class="text-center">Something went wrong! Please try again!</div>');
              enableButtons();
              clearInterval(interval_id);
            }
          });
        }, 3000);
      },
      error: function( e ) {
        result_el.html('<div class="text-center">Something went wrong! Please try again!</div>');
      }
    });
  }

  $("#refresh-data").bind('click', request_fresh_data);
  $('#get-tickets').bind('click', retrieve_data);
});
