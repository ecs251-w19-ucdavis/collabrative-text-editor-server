document.body.style.height = window.innerHeight + "px";
var msgBoard = document.getElementById("messageBoard");
var inputBoard = document.getElementById("inputBoard");
var legendBoard = document.getElementById("legendBoard");
var container = document.getElementById("container");
msgBoard.style.height = container.clientHeight - inputBoard.clientHeight - legendBoard.clientHeight + "px";


var userId = "";
var version = 0;
while (userId == "") {
    userId = prompt("Please enter your UserId", "");
}

var server_socket = io.connect('http://' + document.domain + ':' + location.port);
var doc_ID;
var doc_name;
server_socket.on('connect', function () {
    server_socket.emit('request_doc_list', {"userID": userId});
});

server_socket.on('response_doc_list', function (doc_list) {
    var choice = "";
    var instruction = "";

    for (var i = 0; i < doc_list.length; i++) {
        instruction += i + ". " + doc_list[i]["docName"] + "\n";
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
        server_socket.emit("request_doc_content", {"docName": doc_name, "docID": doc_ID, "userID": userId});
    }
});

server_socket.on('response_create_doc', function (data) {
    doc_ID = data["docID"];
    console.log(doc_ID);
});

server_socket.on("response_doc_content", function (doc_data) {
    document.getElementById("editor").value = doc_data["content"];
    version = doc_data["version"];
});

server_socket.on('join', function (data) {
    var msgBoard = document.getElementById("messageBoard");
    msgBoard.innerHTML += data['msg'] + "<br>";
});

server_socket.on('MSG', function (data) {
    var msgBoard = document.getElementById("messageBoard");
    msgBoard.innerHTML += data["user"] + ": " + data['text'] + "<br>";
});

server_socket.on('DOC', function (data) {
    if (data["user"] != userId) {
        document.getElementById("editor").value = data['doc'];
    }
    version = data['version']
});

server_socket.on('run', function (data) {

    document.getElementById("console").value += data['console'];

});

function keyUpMSG(event) {
    var msg = document.getElementById("input").value;
    var x = event.which || event.keyCode;
    if (x == 13) {
        server_socket.emit('MSG', {
            "user": userId,
            "text": msg,
            "docID": doc_ID
        });
        document.getElementById("input").value = "";
    }
}

function keyPressDOC(event) {
    var doc = document.getElementById("editor").value;
    //server_socket.emit('DOC', {"doc": doc, "user": userId, "docID": doc_ID});
    console.log(event.key);
    var cursorPosition = $('#editor').prop("selectionStart");
    var op = {"op_type": "Insert", "op_char": event.key, "op_index": cursorPosition};
    console.log(op);

    server_socket.emit('DOC', {"op": op, "user": userId, "docID": doc_ID, "version": version});
}


function keyDownDOC(event) {
    if (event.which == 8) {
        var cursorPosition = $('#editor').prop("selectionStart");
        if(cursorPosition == 0) return;
        var op = {"op_type": "Delete", "op_index": cursorPosition,"op_char": ""};
        console.log(op);
        server_socket.emit('DOC', {"op": op, "user": userId, "docID": doc_ID, "version": version});
    }
}

function share() {
    var target = "";
    while (target == "") {
        target = prompt("Please input who you want to share the document with?")
    }
    server_socket.emit("share", {"userID": target, "docID": doc_ID, "docName": doc_name})

}

function save_doc() {
    console.log("saveclicked");
    var doc = document.getElementById("editor").value;
    server_socket.emit("save_doc", {"docID": doc_ID, "doc": doc});
}

function compileRun() {
    save_doc();
    server_socket.emit("run_doc", {"docID": doc_ID, "userID": userId});
}
