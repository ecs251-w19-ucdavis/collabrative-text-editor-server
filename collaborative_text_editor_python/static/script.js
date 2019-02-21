document.body.style.height = window.innerHeight + "px";
var msgBoard = document.getElementById("messageBoard");
var inputBoard = document.getElementById("inputBoard");
var legendBoard = document.getElementById("legendBoard");
var container = document.getElementById("container");
msgBoard.style.height = container.clientHeight - inputBoard.clientHeight - legendBoard.clientHeight + "px";


var userId = "";
while (userId == "") {
    userId = prompt("Please enter your UserId", "");
}
/*
* TODO:
* 1. fetch user's file list from server
* 2. ask user which file to open
* */

// Here we assume userId 1 and 2 are editing file1
// and userId 3 is editing file2
var fileId;
if (userId == "1" || userId == "2") {
    fileId = "file1";
} else {
    fileId = "file2";
}

var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function () {
    socket.emit('join', {"user": userId, 'room': fileId});
});

socket.on('join', function (data) {
    var msgBoard = document.getElementById("messageBoard");
    msgBoard.innerHTML += data['msg'] + "<br>";
});

socket.on('MSG', function (data) {
    var msgBoard = document.getElementById("messageBoard");
    msgBoard.innerHTML += data["user"] + ": " + data['text'] + "<br>";
});

socket.on('DOC', function (data) {
    console.log("receive");
    if (data["user"] != userId) {
        document.getElementById("editor").value = data['doc'];
    }
});


function keyUpMSG(event) {
    var msg = document.getElementById("input").value;
    var x = event.which || event.keyCode;
    if (x == 13) {
        socket.emit('MSG', {"user": userId, "text": msg, 'room': fileId});
        document.getElementById("input").value = "";
    }
}

function keyUpDOC(event) {
    var doc = document.getElementById("editor").value;
    socket.emit('DOC', {"doc": doc, "user": userId, 'room': fileId});
}
