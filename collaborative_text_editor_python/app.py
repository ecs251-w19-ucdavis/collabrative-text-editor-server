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

from model import *

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join')
def joined(message, methods=['GET', 'POST']):
    join_room(message["room"])
    socketio.emit('join', {'msg': message["user"] + ' has entered the room.'}, room=message["room"])


@socketio.on('MSG')
def recieve_msg(json, methods=['GET', 'POST']):
    socketio.emit('MSG', json, room=json["room"])


@socketio.on('DOC')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    socketio.emit('DOC', json, room=json["room"])

@socketio.on('create_file')
def create_file(json, methods = ['GET', 'POST']):
    userID = json["userID"]
    docID = uuid.uuid4()
    docName = json["docName"]

    # check if the file already exists
    if User.query.filter_by(userID=userID, docName=docName):
        #return error message to the client
        pass

    # file does not exist
    user = User(userID=userID, docName=docName, docID=docID)
    with open(docID+".txt","w") as file:
        file.write('')
    db.session.add(user)
    db.commit()

    # client should open the file now

@socketio.on('get_files')
def get_files(json, methods = ['GET', 'POST']):
    userID = json["userID"]
    files = User.query.filter_by(userID=userID)
    response = []
    for file in files:
        response.append(file.docName)
    response = json.dumps(response)
    # return response to the client

@socketio.on('read_file')
def read_file(json, methods = ['GET', 'POST']):
    userID = json["userID"]
    docName = json["docName"]
    user = User.query.filter_by(userID=userID, docName=docName).first()
    docID = user.docID
    with open(docID+".txt","r") as file:
        response = file.read
    response = json.dumps(response)
    # return response to the client

@socketio.on('join_file')
def join_file(json, methods = ['GET', 'POST']):
    userID = json["userID"]
    docName = json["docName"]

    # check if the user is already collaborating this file
    if User.query.filter_by(userID=userID, docName=docName):
        #return error message to the client
        pass

    docID = User.query.filter_by(userID=userID, docName=docName).first().docID
    user = User(userID=userID, docName=docName, docID=docID)
    db.session.add(user)
    db.commit()
    # return response to the client

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
