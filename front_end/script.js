function setCookie(name, value, days) {
  var expires = "";
  if (days) {
    var date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie =
    name + "=" + (value || "") + expires + "; path=/;samesite=strict;";
    // name + "=" + (value || "") + expires + "; path=/;samesite=strict;secure;";

}
//setCookie("token","e61f0e91e73cbf09a5c90b0322f10a5d25aade00",10);

function getCookie(name) {
  let cookie = {};
  document.cookie.split(";").forEach(function (el) {
    let [k, v] = el.split("=");
    cookie[k.trim()] = v;
  });
  return cookie[name];
}
var token = getCookie("token");
var server_url = window.location.origin + "/";
var ws_url = "ws://" + window.location.host + "/";
var requestOptions = {
  mode: "cors",
  method: "POST",
  redirect: "follow",
  headers: {
    Authorization: "Token " + token,
    "Content-Type": "application/json",
  },
};
var socket;

function connect(event) {
  return;
  var url = ws_url + "?token=" + token;
  console.log(url);
  socket = new WebSocket(url);
  socket.onopen = onOpen;
  socket.onmessage = onMessage;
  socket.onclose = onClose;
  socket.onerror = onError;
}

function send(event) {
  socket.send(document.getElementById("body").value);
}

function sendExit(event) {
  socket.send('{"CMD":"EXIT"}');
}

function sendReady(event) {
  socket.send('{"CMD":"READY"}');
}

function onOpen(event) {
  console.log("onOpen");
  document.getElementById("message_input").focus();
}

function handelOpponentDetails(opponent_details) {
  console.log(opponent_details);
  // CHANGED:changed display to none
  document.getElementById("info_message").style.display = "none"; // or visible|hidden|collapse|initial|inherit
  document.getElementById("opponent_name").innerHTML =
    opponent_details["username"];
  document.getElementById("opponent_age").innerHTML = opponent_details["age"];
  document.getElementById("opponent_bio").innerHTML = opponent_details["bio"];

  if (opponent_details["gender"] == "m") {
    document.getElementById("opponent_gender").innerHTML = "Male";
  } else {
    document.getElementById("opponent_gender").innerHTML = "Female";
  }
  document.getElementById("chat_menu").style.display = "initial";
  document.getElementById("chat_box").style.display = "initial";
  console.log("done");
}

function receiveMessage(message_text) {
  document.getElementById("chat_window").innerHTML += `
    <div class="row mb-2">
    <li class="in">
        <div class="chat-body">
            <div class="chat-message" id="message${idCount}">
            </div></div></li></div>`;
  var msg = document.createElement("p");
  // Jaga - changed
   msg.classList.add("text-wrap", "fs-6", "fst-italic", "text-start");
  var msg_content = document.createTextNode(message_text);
  msg.appendChild(msg_content);
  var element = document.getElementById("message" + idCount);
  element.appendChild(msg);
  idCount++;
}

function handleError() {
  document.getElementById("info_message").innerHTML = "Error occurred";
  socket.close();
}

function onMessage(event) {
  var received_data = JSON.parse(event.data);
  var command = received_data["CMD"];
  console.log("Message: Data received from server:" + command);
  if (command == "WAIT_FOR_OPPONENT") {
    document.getElementById("info_message").innerHTML = "Finding a match...";
  } else if (command == "OPPONENT_DETAILS") {
    handelOpponentDetails(received_data["data"]);
  } else if (command == "MSG") {
    receiveMessage(received_data["data"]);
  } else if (command == "OPPONENT_LEFT") {
    showOpponentLeftMenu();
  }
}

function onClose(event) {
  console.log("onClose");
  if (event.wasClean) {
    console.log(
      `[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`
    );
  } else {
    console.log("[close] Connection died");
    document.getElementById("info_message").innerHTML =
      "Could not connect to server";
  }
}

function onError(event) {
  console.log("onError");
  document.getElementById("info_message").innerHTML =
    "Could not connect to server";
}

var idCount = 0;

function sendMessage(text) {
//   var text = document.getElementById("message_input").value;
  if (text == "" || text.length == 0 || text == null) {
    console.log("Message field cannot be empty");
    document.getElementById("message_input").focus();
    return;
  } else {
    var full_message = '{"CMD":"MSG","data":"' + text + '"}';
    console.log(full_message);
    // socket.send(full_message);
    document.getElementById("chat_window").innerHTML += `
    <div class="row mb-2">
    <li class="out">
        <div class="chat-body">
            <div class="chat-message" id="message${idCount}">
            </div></div></li></div>`;
    var msg = document.createElement("p");
    // Jaga - changed the fs to 6
    msg.classList.add("text-wrap", "fs-6", "fst-italic", "text-start");
    var msg_content = document.createTextNode(text);
    msg.appendChild(msg_content);
    var element = document.getElementById("message" + idCount);
    element.appendChild(msg);
    idCount++;
  }
  //clear the input field
  document.getElementById("message_input").value = "";
}

sendMessage("Lorem ipsum dolor, sit amet consectetur adipisicing elit. Reprehenderit explicabo dignissimos, facere ea dolorum modi eligendi obcaecati tenetur aut iure esse molestias, commodi laboriosam inventore sapiente vel, adipisci facilis cumque!")
receiveMessage("hi sit amet consectetur adipisicing elit. Reprehenderit explicabo dignissimos, facere ea dolorum modi eligendi obcaecati tenetur aut iure esse molestias, commodi laboriosam inventore sapiente vel, adipisci facilis cumque")
sendMessage("Hi")
receiveMessage("hello sit amet consectetur adipisicing elit. Reprehenderit explicabo dignissimos, facere ea dolorum modi eligendi obcaecati tenetur aut iure esse molestias, commodi laboriosam inventore sapiente vel, adipisci facilis cumque")
sendMessage("content")

sendMessage("Lorem ipsum dolor, sit amet consectetur adipisicing elit. Reprehenderit explicabo dignissimos, facere ea dolorum modi eligendi obcaecati tenetur aut iure esse molestias, commodi laboriosam inventore sapiente vel, adipisci facilis cumque!")
receiveMessage("hi sit amet consectetur adipisicing elit. Reprehenderit explicabo dignissimos, facere ea dolorum modi eligendi obcaecati tenetur aut iure esse molestias, commodi laboriosam inventore sapiente vel, adipisci facilis cumque")
sendMessage("Hi")
receiveMessage("hello sit amet consectetur adipisicing elit. Reprehenderit explicabo dignissimos, facere ea dolorum modi eligendi obcaecati tenetur aut iure esse molestias, commodi laboriosam inventore sapiente vel, adipisci facilis cumque")
sendMessage("content")


// function showReportMenu() {
//   document.getElementById("report_menu").style.display = "initial";
//   return false;
// }

// function hideReportMenu() {
//   document.getElementById("report_menu").style.display = "none";
// }

function hideChatUI() {
  document.getElementById("chat_menu").style.display = "none";
  document.getElementById("chat_box").style.display = "none";
  document.getElementById("chat_window").style.display = "none";
}

function nextUserAfterReport() {
  // simply reload the page.Improvements later
  window.location.reload();
}

function showOpponentLeftMenu() {
  // hide all divs except "opponent_left_menu"
  document.getElementById("chat_menu").style.display = "none";
  document.getElementById("chat_box").style.display = "none";
  document.getElementById("chat_window").style.display = "none";
  document.getElementById("report_menu").style.display = "none";
  document.getElementById("after_report_menu").style.display = "none";
  document.getElementById("info_message").style.display = "none";
  document.getElementById("opponent_left_menu").style.display = "block";
}

function exitChat() {
  window.location.assign(server_url + "start_chat/");
}

function showAfterReportMenu() {
  document.getElementById("after_report_menu").style.display = "block";
}
// called when user presses "next user" in the middle of the chat
function showNextUserMenu() {
  if (confirm("Are you sure?")) {
    window.location.reload();
  } else {
    // Do nothing!
  }
}

// called when user presses "Exit chat" in the middle of the chat
function showExitMenu() {
  if (confirm("Are you sure?")) {
    window.location.assign(server_url + "start_chat/");
  } else {
    // Do nothing!
  }
}

function submitReport() {
  var report_id = "";
  var report_message = "";
  var report_text = document.getElementById("report_reason_others_text").value;

  if (document.getElementById("report_reason3").checked) {
    console.log("3 clicked");
    // when report_id is 3, report_text is mandatory
    if (report_text.length == 0) {
      document.getElementById("report_others_warn").innerHTML =
        "Please explain the reason";
      return;
    }
    console.log("report text is..", report_text);
    report_id = 3;
  } else {
    document.getElementById("report_others_warn").innerHTML = "";
    if (document.getElementById("report_reason0").checked) {
      console.log("0 selected");
      report_id = "0";
    } else if (document.getElementById("report_reason1").checked) {
      console.log("1 selected");
      report_id = "1";
    } else if (document.getElementById("report_reason2").checked) {
      console.log("2 selected");
      report_id = "2";
    }
  }

  if (report_text.length == 0) {
    report_message = '{"CMD":"REPORT","report_id":"' + report_id + '"}';
  } else {
    report_message =
      '{"CMD":"REPORT","report_id":"' +
      report_id +
      '","report_text":"' +
      report_text +
      '"}';
  }
  socket.send(report_message);
  console.log("report sent", report_message);
  // hideReportMenu();
  hideChatUI();
  showAfterReportMenu();
  return false;
}

window.onload = function () {
  // connect only after HTML is loaded. Else there wont be any document to modify
  connect();
};
