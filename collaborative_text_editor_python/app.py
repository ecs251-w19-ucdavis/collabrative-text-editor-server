from flask import Flask, render_template
from flask_socketio import SocketIO, join_room
from flask_sqlalchemy import SQLAlchemy
from flask import session
import uuid
import json


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


db.create_all()
db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('MSG')
def recieve_msg(json, methods=['GET', 'POST']):
    socketio.emit('MSG', json, room=json["docID"])


@socketio.on('DOC')
def receive_doc_update(json, methods=['GET', 'POST']):
    document = Document.query.filter_by(docID=json["docID"]).first()
    document.content = json["doc"]
    db.session.commit()
    socketio.emit('DOC', json, room=json["docID"])


@socketio.on('create_new_doc')
def create_file(json, methods=['GET', 'POST']):
    userID = json["userID"]
    docID = str(uuid.uuid4())
    docName = json["docName"]
    join_room(docID)

    user = User(userID=userID, docName=docName, docID=docID)
    with open(docID + ".txt", "w") as file:
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
    with open(docID + ".txt", "w") as file:
        file.write(json["doc"])
        file.close()

@socketio.on('transform')
def commit_transform(operations):
    if str(operations['op1_type']) == "Insert":
        op1 = [{"retain": int(operations['op1_index'])}, {"insert": str(operations['op1_string'])}]
    if str(operations['op1_type']) == "Delete":
        op1 = [{"retain": int(operations['op1_index'])}, {"delete": int(operations['op1_string'])}]

    if str(operations['op2_type']) == "Insert":
        op2 = [{"retain": int(operations['op2_index'])}, {"insert": str(operations['op2_string'])}]
    if str(operations['op2_type']) == "Delete":
        op2 = [{"retain": int(operations['op2_index'])}, {"delete": int(operations['op2_string'])}]

    OT = OT_String("verbose")

    new_ops = OT.transform(op1, op2)
    emit('new_ops', {'op1': str(op1), 'op2': str(op2), 'op1_prime': str(new_ops[0]), 'op2_prime': str(new_ops[1])})
    emit('apply_original', {'op1_index': int(op1[0]['retain']), 'op1_string': str(op1[1]['insert']), 'op2_index': int(op2[0]['retain']), 'op2_string': str(op2[1]['insert'])})
    emit('apply_transformed', {'op1_index': int(operations['op1_index']), 'op1_string': str(operations['op1_string']), 'op2_index': int(operations['op2_index']), 'op2_string': str(operations['op2_string'])})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
