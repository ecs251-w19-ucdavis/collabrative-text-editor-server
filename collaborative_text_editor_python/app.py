from __future__ import print_function
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room
from flask_sqlalchemy import SQLAlchemy
from flask import session
import uuid
import subprocess
import json
import sys
from threading import Lock
from wordsmiths import OT_String
from collections import namedtuple

# Basic op for Myer's algorithm
Keep = namedtuple('Keep', ['line'])
Insert = namedtuple('Insert', ['line'])
Remove = namedtuple('Remove', ['line'])
Frontier = namedtuple('Frontier', ['x', 'history'])


def myers_diff(a_lines, b_lines):
    # build the frontier in the edit graph
    frontier = {1: Frontier(0, [])}
    def one(idx):
        return idx - 1
    a_max = len(a_lines)
    b_max = len(b_lines)
    for d in range(0, a_max + b_max + 1):
        for k in range(-d, d + 1, 2):
            # Search point will go down or to the right
            go_down = (k == -d or
                       (k != d and frontier[k - 1].x < frontier[k + 1].x))
            if go_down:
                old_x, history = frontier[k + 1]
                x = old_x
            else:
                old_x, history = frontier[k - 1]
                x = old_x + 1
            # Get the old history
            history = history[:]
            y = x - k
            # Start at the invalid point (0, 0)
            if 1 <= y <= b_max and go_down:
                history.append(Insert(b_lines[one(y)]))
            elif 1 <= x <= a_max:
                history.append(Remove(a_lines[one(x)]))
            # Diagnoal moves
            while x < a_max and y < b_max and a_lines[one(x + 1)] == b_lines[one(y + 1)]:
                x += 1
                y += 1
                history.append(Keep(a_lines[one(x)]))
            if x >= a_max and y >= b_max:
                return history
            else:
                frontier[k] = Frontier(x, history)
    assert False, '---Error, Could not find edit script---'


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
        if self.head == None:
            self.head = 0

    def pop(self):
        print(self.queue)
        temp = self.queue[self.head]
        self.head += 1
        return temp


db.create_all()
db.session.commit()

# global variables
queue = MyQueue()
lock = Lock()
server_version = 0


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('MSG')
def recieve_msg(json):
    socketio.emit('MSG', json, room=json["docID"])


@socketio.on('DOC')
def receive_doc_update(json):
    global queue
    global lock
    global server_version

    doc_on_switch = str(json['option'])
    print('doc:' + str(doc_on_switch))

    if doc_on_switch == '0':
        # adds common version with doc in and doc out
        document = Document.query.filter_by(docID=json["docID"]).first()
        document.content = json["doc"]
        db.session.commit()
        socketio.emit('DOC', json, room=json["docID"])

    elif doc_on_switch == '1':
        # OT algorithms
        # successfully debug version of OTs.
        temp = json['op']
        op_type = temp['op_type']
        # for deletion, op_char is empty
        op_char = temp['op_char']
        op_index = temp['op_index']
        version = int(json['version'])

        if op_type == "Insert":
            op = [{"retain": int(op_index)}, {"insert": op_char}]
        if op_type == "Delete":
            op = [{"retain": int(op_index) - 1}, {"delete": 1}]

        with lock:
            queue.push((op, version))
        with lock:
            (cur_op, cur_version) = queue.pop()
        # performing transformation until the op is sync with the current version on server
        while cur_version < server_version:

            OT = OT_String("verbose")
            prev_ops = MyQueue.queue[cur_version][0]
            print('Op1:' + str(prev_ops))
            print('Op2:' + str(op))
            op = OT.transform(prev_ops, op)[1]

            # print('---testing myer op operation--')
            # op1 = str(prev_ops)
            # op2 = str(op)
            # diff = myers_diff(op1, op2)
            # for elem in diff:
            #     if isinstance(elem, Keep):
            #         print(' ' + elem.line)
            #     elif isinstance(elem, Insert):
            #         print('+' + elem.line)
            #     else:
            #         print('-' + elem.line)

            print('Op_tranform:' + str(op))
            # -------Revised OT algorithm--------------------
            # We only pick the op2 here,
            #    op1: xab op2:aby
            #       =>
            #    transform: xaby
            #       =>
            #    Write to Doc
            retain = {'retain': op['index']}
            op.pop('index')
            op = [retain, op]
            print('cur_op:' + str(op))
            cur_version += 1

        index = op[0]["retain"]
        cur_op = op[1]
        document = Document.query.filter_by(docID=json["docID"]).first()
        content = document.content

        if "insert" in cur_op:
            content = content[:index] + cur_op["insert"] + content[index:]
            # print("content:"+content)
        elif "delete" in cur_op:
            content = content[:index] + content[index + 1:]

        document.content = content
        db.session.commit()
        with lock:
            server_version += 1
        # print("version:"+str(server_version))
        json['doc'] = document.content
        json['version'] = str(server_version)
        # print(json['version'])
        print("content: " + json['doc'])
        socketio.emit('DOC', json, room=json["docID"])

    elif doc_on_switch == '2':
        # -------Revised Myer diff algorithm--------------------
        # successfully implement for diff patch algorithms.
        document = Document.query.filter_by(docID=json["docID"]).first()
        document.content = json["doc"]
        # should be init state from Client A from front end
        init_state = str(document.content)
        # should be update_op from Client B from front end
        update_state = str(document.content)
        print('---Myer op operation to get the diff--')
        diff = myers_diff(init_state, update_state)
        for elem in diff:
            if isinstance(elem, Keep):
                print(' ' + elem.line)
            elif isinstance(elem, Insert):
                print('+' + elem.line)
            else:
                print('-' + elem.line)
        # should update here according to diff from the Myer's algorithm
        document.content = update_state
        # submit update
        json['doc'] = document.content
        db.session.commit()
        socketio.emit('DOC', json, room=json["docID"])


@socketio.on('create_new_doc')
def create_file(json):
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

    socketio.emit('response_create_doc', {"docID": docID}, room=userID)
    # client should open the file now


@socketio.on('request_doc_list')
def get_files(json):
    userID = json["userID"]
    join_room(userID)
    files = User.query.filter_by(userID=userID)
    response = []
    for file in files:
        response.append({"docName": file.docName, "docID": file.docID})
    socketio.emit('response_doc_list', response, room=userID)


@socketio.on('request_doc_content')
def read_file(json, methods=['GET', 'POST']):
    global server_version
    docID = json["docID"]
    userID = json["userID"]
    join_room(docID)
    response = Document.query.filter_by(docID=docID).first().content
    socketio.emit('response_doc_content', {"docID": docID, "content": response, "version": server_version}, room=userID)
    socketio.emit('join', {'msg': userID + ' has entered the room.'}, room=docID)


@socketio.on('share')
def join_file(json):
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
def save_file(json):
    docID = json["docID"]
    print("save " + docID)
    with open(docID + ".c", "w") as file:
        file.write(json["doc"])
        file.close()


@socketio.on('run_doc')
def run_file(json):
    docID = json["docID"]
    try:
        output1 = subprocess.check_output(["gcc", "-o", docID, docID + ".c"], stderr=subprocess.STDOUT, timeout=10)
        socketio.emit('run', {'console': output1}, room=json["userID"])
    except subprocess.CalledProcessError as e:
        output1 = e.output
        socketio.emit('run', {'console': output1}, room=json["userID"])
        return

    try:
        output2 = subprocess.check_output([docID], stderr=subprocess.STDOUT, timeout=10)
        socketio.emit('run', {'console': output2}, room=json["userID"])
    except subprocess.CalledProcessError as e:
        output2 = e.output
        socketio.emit('run', {'console': output2}, room=json["userID"])
        return


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
