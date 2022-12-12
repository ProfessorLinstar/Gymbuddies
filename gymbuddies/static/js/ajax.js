let refreshid;
let ajaxtimeout = 10000;
let refreshinterval = 1000;

let lastrefreshed = 0;
let refreshing = false;
let request = null;
let getrequest = null;
let postrequest = null;


function showError(jqXHR) {
  let backdrop = "static";
  let message = "Oops! An unexpected error occurred. Please refresh.";
  console.log(jqXHR);
  if (jqXHR.responseJSON !== undefined) {
    if (jqXHR.responseJSON.noRefresh) {
      backdrop = true;
    } else {
      window.clearInterval(refreshid);
      console.log("clearing interval!");
    }
    if (jqXHR.responseJSON.message !== undefined) message = jqXHR.responseJSON.message;
  }
  $("#errorPopup").modal({"backdrop": backdrop});
  $("#errorPopupSpan").html(message);
  $("#errorPopup").modal("show");
  lastrefreshed = 0;
}


function fillCard(response) {
  console.log("got a response");
  $('#userPopup').html(response);
}


function getCard(requestid, url) {
  if (getrequest != null) {
    console.log("aborting other getrequests!");
  }

 getrequest = $.ajax({
    type: 'GET',
    data: { "requestid": requestid },
    url: url,
    success: fillCard,
    complete: function() { getrequest = null; },
    error: function() { console.log("getCard failed!"); },
    timeout: ajaxtimeout,
  });
}


function unmatchCard(response) {
  console.log("got a response");
  $('#unmatchModal').html(response);
}

function getunmatchCard(requestid, url) {
  if (getrequest != null) {
    console.log("aborting other getrequests!");
  }

  console.log("making getrequest with requestid", requestid)
 getrequest = $.ajax({
    type: 'GET',
    data: { "requestid": requestid },
    url: url,
    success: unmatchCard,
    complete: function() { getrequest = null; },
    error: function() { console.log("getCard failed!"); },
    timeout: ajaxtimeout,
  });
}

// used as the 'success' property of an ajax request argument. Requires an
// 'id' property to be provided to indicate where to write the response.
function refresh(response, id, updatelastrefreshed) {
  if (response) {
    if (updatelastrefreshed) lastrefreshed = Date.now();
    console.log("refresh is", updatelastrefreshed);
    $(id).html(response);
    console.log("making an update now for", id, "at time", new Date(Date.now()));
  }
  console.log("success: no update required.");
}

// used as the 'error' property of an ajax request argument.
function error(xhr, textStatus, errorThrown) {
  console.log(xhr, textStatus, errorThrown);
  if (textStatus == "timeout") {
    ajaxtimeout *= 2;
    console.log("doubled ajaxtimeout to ", ajaxtimeout);
  } else if (textStatus != "abort") {
    showError(xhr);
  }
}

function act(url, id, requestid, action) {
  if (postrequest != null) {
    console.log("postrequest already in process! breaking!");
    return;
  }

  $("body").addClass("wait");
  postrequest = $.ajax({
    type: "POST",
    data: { "requestid": requestid, "action": action },
    url: url,
    success: function(response) { 
      refresh(response, id, false); },
    complete: function() { postrequest = null; $("body").removeClass("wait"); },
    error: error,
    timeout: ajaxtimeout,
  });
}

function act2(url, requestid) {
  if (getrequest != null) {
    console.log("postrequest already in process! breaking!");
    return;
  }

  $("body").addClass("wait");
  getrequest = $.ajax({
    type: "GET",
    data: { "requestid": requestid},
    url: url,
    success: function(response) { 
      $('#unmatchModal').html(response); 
      $('#unmatchConfirm').modal('show');
    },
    complete: function() { postrequest = null; $("body").removeClass("wait"); },
    error: error,
    timeout: ajaxtimeout,
  });
}

function refreshMultiple(url_ids) {
  const responses = [];
  let successes = 0;
  let completed = 0;

  console.log("url_id", url_ids)
  if (refreshing) {
    console.log("refresh detected!");
    return;
  }
  refreshing = true;


  for (let i = 0; i < url_ids.length; i++) {
    const url = url_ids[i][0];
    console.log("why is this happening???", $.ajax);
    getrequest = $.ajax({
      type: "GET",
      data: { "lastrefreshed": lastrefreshed },
      url: url,
      success: function(response) {
        responses[i] = response;
        if (++successes == url_ids.length) {
          for (let j = 0; j < responses.length; j++)
            refresh(responses[j], url_ids[j][1], j == responses.length - 1)
        }
      },
      complete: function() {
        if (++completed == url_ids.length) refreshing = false;
      },
      error: error,
      timeout: ajaxtimeout,
    })
  }

}

function setup_refresh(url_ids) {
  if (refreshid) {
    console.log("do not call me multiple times!");
    return;
  }
  refreshMultiple(url_ids);
  refreshid = window.setInterval(refreshMultiple, refreshinterval, url_ids)
}
