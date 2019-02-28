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

var server_socket = io.connect('http://' + document.domain + ':' + location.port);
var doc_socket = io("/");
var doc_ID;
var doc_name;
server_socket.on('connect', function () {
    server_socket.emit('request_doc_list', {"userID": userId});
});

server_socket.on('response_doc_list', function (doc_list) {
    var choice = "";
    var instruction = "";

    for (var i = 0; i < doc_list.length; i++) {
        instruction += i + ". " + doc_list[i]["docName"];
    }
    instruction += doc_list.length + ". " + "Create new document";
    while (choice == "" || parseInt(choice) > doc_list.length) {
        choice = prompt(instruction, "");
    }

    if (parseInt(choice) == doc_list.length) {
        var new_doc_name = "";
        while (new_doc_name == "") {
            new_doc_name = prompt("Please input your new document name", "");
            for (var i = 0; i < doc_list.length; i++) {
                if (new_doc_name == doc_list[i]["docName"]) {
                    alert("Duplicated document name!");
                    break;
                }
            }
        }
        doc_name = new_doc_name;
        server_socket.emit("create_new_doc", {"userID": userId, "docName": new_doc_name});
    } else {
        doc_ID = doc_list[parseInt(choice)]["docID"];
        doc_name = doc_list[parseInt(choice)]["docName"]
        server_socket.emit("request_doc_content", {"docName":doc_name, "docID":doc_ID, "userID":userId});
    }
});

server_socket.on('response_create_doc', function (data) {
    doc_ID = data["docID"];
    doc_socket = io("/" + data["docID"]);
    defineServerCommunication(doc_socket)
});

server_socket.on("response_doc_content", function (doc_data) {
    document.getElementById("editor").value = doc_data["content"];
    doc_socket = io("/" + doc_data["docID"]);
    defineServerCommunication(doc_socket);
});

function defineServerCommunication(doc_socket) {
    doc_socket.on('connect', function () {
        doc_socket.emit('join', {"user": userId, "docID": doc_ID});
    });

    doc_socket.on('join', function (data) {
        var msgBoard = document.getElementById("messageBoard");
        msgBoard.innerHTML += data['msg'] + "<br>";
    });

    doc_socket.on('MSG', function (data) {
        var msgBoard = document.getElementById("messageBoard");
        msgBoard.innerHTML += data["user"] + ": " + data['text'] + "<br>";
    });

    doc_socket.on('DOC', function (data) {
        if (data["user"] != userId) {
            document.getElementById("editor").value = data['doc'];
        }
    });
}

function keyUpMSG(event) {
    var msg = document.getElementById("input").value;
    var x = event.which || event.keyCode;
    if (x == 13) {
        doc_socket.emit('MSG', {
            "user": userId,
            "text": msg,
            "docID": doc_ID
        }, namespace = "/" + doc_ID);
        document.getElementById("input").value = "";
    }
}

function keyUpDOC(event) {
    var doc = document.getElementById("editor").value;
    doc_socket.emit('DOC', {"doc": doc, "user": userId, "docID": doc_ID});
}

function share() {
    var target = "";
    while (target == "") {
        target = prompt("Please input who you want to share the document with?")
    }
    server_socket.emit("share", {"userID": target, "docID": doc_ID, "docName": doc_name})

}

function save_doc() {
    var doc = document.getElementById("editor").value;
    server_socket.emit("save", {"docID": doc_ID, "doc": doc});
}