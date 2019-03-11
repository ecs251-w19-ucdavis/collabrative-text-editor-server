from flask import Flask, render_template
from flask_socketio import SocketIO, join_room
from flask_sqlalchemy import SQLAlchemy
from flask import session
import uuid
import subprocess
import json
from threading import Lock
from wordsmiths import OT_String


app = Flask(__name__)
socketio = SocketIO(app)

# db object
db = SQLAlchemy(app)

class User(db.Model):
    userID = db.Column(db.String, primary_key=True)
    docName = db.Column(db.String, primary_key=True, nullable=True)
    docID = db.Column(db.String, nullable=True)


class Document(db.Model):
    docID = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)

class MyQueue():
    queue = []
    head = None

    def push(self, op):
        self.queue.append(op)
        if head == None:
            self.head = 0
        else:
            self.head += 1

    def pop(self):
        temp = self.queue[head]
        head += 1
        return temp

db.create_all()
db.session.commit()

# global variables
queue = MyQueue()
lock = Lock()
version = 0

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('MSG')
def recieve_msg(json, methods=['GET', 'POST']):
    socketio.emit('MSG', json, room=json["docID"])


@socketio.on('DOC')
def receive_doc_update(json, methods=['GET', 'POST']):
    global queue
    global lock
    global version

    op_type = json['op_type']
    # for deletion, op_char is empty
    op_char = json['op_char']
    op_index = json['op_index']
    version = int(json['version'])

    if op_type == "Insert":
        op = [{"retain": int(op_index)}, {"insert": op_char}]
    if op_type == "Delete":
        op = [{"retain": int(op_index)}, {"delete": 1}]

    with lock:
        queue.push((op, version))
    with lock:
        (cur_op, cur_version) = queue.pop()

    # performing transformation until the op is sync with the current version on server
    while cur_version < version:
        OT = OT_String("verbose")
        prev_ops = MyQueue.queue[cur_version][0]
        # OT.transform will return a tuple containing op1_prime and op2_prime
        cur_op = OT.transform(prev_ops, cur_op)[1]
        cur_version += 1

    index = op[0]["retain"]
    cur_op = op[1]
    document = Document.query.filter_by(docID=json["docID"]).first()
    content = document.content

    if "insert" in cur_op:
        content = content[:index] + cur_op["insert"] + content[index:]
    elif "delete" in cur_op:
        content = content[:index] + content[index+1:]

    document.content = content
    db.session.commit()
    with lock:
        version += 1

    socketio.emit('DOC', json, room=json["docID"])


@socketio.on('create_new_doc')
def create_file(json, methods=['GET', 'POST']):
    userID = json["userID"]
    docID = str(uuid.uuid4())
    docName = json["docName"]
    join_room(docID)

    user = User(userID=userID, docName=docName, docID=docID)
    with open(docID + ".c", "w") as file:
        file.write('')
        file.close()
    db.session.add(user)
    doc = Document(docID=docID, content="")
    db.session.add(doc)
    db.session.commit()

    socketio.emit('response_create_doc', {"docID":docID},room=userID)
    # client should open the file now


@socketio.on('request_doc_list')
def get_files(json, methods=['GET', 'POST']):
    userID = json["userID"]
    join_room(userID)
    files = User.query.filter_by(userID=userID)
    response = []
    for file in files:
        response.append({"docName": file.docName, "docID": file.docID})
    socketio.emit('response_doc_list', response,room=userID)


@socketio.on('request_doc_content')
def read_file(json, methods=['GET', 'POST']):
    docID = json["docID"]
    userID = json["userID"]
    join_room(docID)
    response = Document.query.filter_by(docID=docID).first().content
    socketio.emit('response_doc_content', {"docID":docID, "content":response},room=userID)
    socketio.emit('join', {'msg': userID + ' has entered the room.'}, room=docID)


@socketio.on('share')
def join_file(json, methods=['GET', 'POST']):
    userID = json["userID"]
    docName = json["docName"]
    docID = json["docID"]

    # check if the user is already collaborating this file
    if User.query.filter_by(userID=userID, docName=docName, docID=docID).all():
        return

    user = User(userID=userID, docName=docName, docID=docID)
    db.session.add(user)
    db.session.commit()


@socketio.on('save_doc')
def save_file(json, methods=['GET', 'POST']):
    docID = json["docID"]
    print("save " + docID)
    with open(docID + ".c", "w") as file:
        file.write(json["doc"])
        file.close()


@socketio.on('run_doc')
def run_file(json, methods=['GET', 'POST']):
    docID = json["docID"]
    try:
        output1 = subprocess.check_output(["gcc", "-o", docID, docID+".c"],stderr=subprocess.STDOUT,timeout=10)
        socketio.emit('run', {'console': output1}, room=json["userID"])
    except subprocess.CalledProcessError as e:
        output1 = e.output
        socketio.emit('run', {'console': output1}, room=json["userID"])
        return

    try:
        output2 = subprocess.check_output([docID],stderr=subprocess.STDOUT,timeout=10)
        socketio.emit('run', {'console': output2}, room=json["userID"])
    except subprocess.CalledProcessError as e:
        output2 = e.output
        socketio.emit('run', {'console': output2}, room=json["userID"])
        return




if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
